from rest_framework import serializers


class MedicationItemSerializer(serializers.Serializer):
    name = serializers.CharField()
    is_new = serializers.BooleanField()

class MedicationAnalysisRequestSerializer(serializers.Serializer):
    language = serializers.CharField(default="english")
    patient_age = serializers.IntegerField()
    conditions = serializers.CharField()
    medications = MedicationItemSerializer(many=True)