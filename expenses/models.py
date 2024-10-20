from django.db import models
import logging
from django.db import transaction  # Add this import

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.name  # Updated to use 'name' since 'username' doesn't exist
    
class Balance(models.Model):
    from_user = models.ForeignKey(User, related_name="balance_from", on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name="balance_to", on_delete=models.CASCADE)
    amount = models.FloatField()

    def __str__(self):
        return f"{self.from_user.name} owes {self.to_user.name} {self.amount}"  # Updated to use 'name'
    
logger = logging.getLogger(__name__)

class Expense(models.Model):
    SPLIT_METHODS = [
        ('equal', 'Equal'),
        ('exact', 'Exact'),
        ('percentage', 'Percentage'),
    ]

    payer = models.ForeignKey(User, related_name="expenses_paid", on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name="shared_expenses")
    amount = models.FloatField()
    split_method = models.CharField(max_length=20, choices=SPLIT_METHODS)
    exact_splits = models.JSONField(null=True, blank=True)
    percentage_splits = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def split_expense(self):
        logger.info(f"Starting to split expense {self.id}")
        try:
            if self.split_method == 'equal':
                participant_count = self.participants.count()
                if participant_count == 0:
                    raise ValueError("No participants found for the expense")
                
                per_person = self.amount / participant_count
                logger.info(f"Equal split: {per_person} per person among {participant_count} participants")
                
                for participant in self.participants.all():
                    self.update_balance(participant, per_person)

            elif self.split_method == 'exact':
                if not self.exact_splits:
                    raise ValueError("Exact splits data is required")
                
                for participant_id, exact_amount in self.exact_splits.items():
                    try:
                        participant = User.objects.get(id=participant_id)
                        self.update_balance(participant, float(exact_amount))
                    except User.DoesNotExist:
                        raise ValueError(f"User with ID {participant_id} not found")

            elif self.split_method == 'percentage':
                if not self.percentage_splits:
                    raise ValueError("Percentage splits data is required")
                
                for participant_id, percentage in self.percentage_splits.items():
                    try:
                        participant = User.objects.get(id=participant_id)
                        owed_amount = (self.amount * float(percentage) / 100)
                        self.update_balance(participant, owed_amount)
                    except User.DoesNotExist:
                        raise ValueError(f"User with ID {participant_id} not found")

        except Exception as e:
            logger.error(f"Error in split_expense: {str(e)}")
            raise

    def update_balance(self, participant, amount):
        logger.info(f"Updating balance: {participant.id} owes {amount} to {self.payer.id}")
        
        if participant == self.payer:
            logger.info("Skipping balance update for payer")
            return

        try:
            with transaction.atomic():
                # Get or create balance
                balance, created = Balance.objects.get_or_create(
                    from_user=participant,
                    to_user=self.payer,
                    defaults={'amount': amount}
                )

                if not created:
                    balance.amount += amount
                    balance.save()

                logger.info(f"Balance updated successfully: {balance.amount}")

                # Handle reverse balance
                reverse_balance, created = Balance.objects.get_or_create(
                    from_user=self.payer,
                    to_user=participant,
                    defaults={'amount': 0}
                )

                if reverse_balance.amount > 0:
                    if reverse_balance.amount >= amount:
                        reverse_balance.amount -= amount
                        reverse_balance.save()
                    else:
                        amount -= reverse_balance.amount
                        reverse_balance.amount = 0
                        reverse_balance.save()
                        balance.amount = amount
                        balance.save()

        except Exception as e:
            logger.error(f"Error in update_balance: {str(e)}")
            raise
