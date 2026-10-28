from rest_framework import serializers


class ProcessVideoSerializer(serializers.Serializer):
    url = serializers.URLField()


class AskQuestionSerializer(serializers.Serializer):
    question = serializers.CharField(
        max_length=2000,
        trim_whitespace=True,
    )
    language = serializers.CharField(
        max_length=30,
        default="Arabic",
    )