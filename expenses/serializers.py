# serializers.py
from rest_framework import serializers
from .models import User, Expense
import logging
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'mobile']
        
        
logger = logging.getLogger(__name__)

class ExpenseSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=True)
    
    class Meta:
        model = Expense
        fields = ['id', 'payer', 'participants', 'amount', 'split_method', 'exact_splits', 'percentage_splits']

    def validate(self, data):
        logger.info(f"Validating expense data: {data}")
        
        try:
            payer = User.objects.get(id=data['payer'].id)
            logger.info(f"Payer validated: {payer.id}")
        except User.DoesNotExist:
            raise serializers.ValidationError({"payer": "Payer user does not exist"})

        participant_ids = [p.id for p in data['participants']]
        logger.info(f"Validating participants: {participant_ids}")
        
        existing_participants = User.objects.filter(id__in=participant_ids)
        if len(existing_participants) != len(participant_ids):
            missing_ids = set(participant_ids) - set(p.id for p in existing_participants)
            raise serializers.ValidationError({"participants": f"Users with IDs {missing_ids} do not exist"})

        if data['amount'] <= 0:
            raise serializers.ValidationError({"amount": "Amount must be greater than 0"})

        if data['split_method'] not in ['equal', 'exact', 'percentage']:
            raise serializers.ValidationError({"split_method": "Invalid split method"})

        if data['split_method'] == 'exact':
            if not data.get('exact_splits'):
                raise serializers.ValidationError({"exact_splits": "Exact splits are required"})
            total = sum(float(amount) for amount in data['exact_splits'].values())
            if abs(total - data['amount']) > 0.01: 
                raise serializers.ValidationError({"exact_splits": "Sum of exact splits must equal total amount"})

        if data['split_method'] == 'percentage':
            if not data.get('percentage_splits'):
                raise serializers.ValidationError({"percentage_splits": "Percentage splits are required"})
            total = sum(float(percentage) for percentage in data['percentage_splits'].values())
            if abs(total - 100) > 0.01:
                raise serializers.ValidationError({"percentage_splits": "Percentages must sum to 100"})

        return data