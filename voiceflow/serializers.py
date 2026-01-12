from rest_framework import serializers

class KBChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=4000)
    chunk_limit = serializers.IntegerField(required=False, min_value=1, max_value=20, default=6)
