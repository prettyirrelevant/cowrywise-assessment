from rest_framework import serializers

from librarian.apps.books.models import Book, BorrowedBook


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'id',
            'isbn',
            'title',
            'author',
            'added_by',
            'category',
            'publisher',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'added_by': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }

    def create(self, validated_data):
        validated_data['added_by'] = self.context['request'].user.id
        return Book.objects.create(**validated_data)


class BorrowedBookSerializer(serializers.ModelSerializer):
    book = BookSerializer()

    class Meta:
        model = BorrowedBook
        fields = [
            'book',
            'created_at',
            'updated_at',
            'is_returned',
            'actual_return_date',
            'proposed_return_date',
        ]


class UserSerializer(serializers.Serializer):
    id = serializers.CharField()
    email = serializers.EmailField()
    last_name = serializers.CharField()
    first_name = serializers.CharField()


class DummySerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = serializers.JSONField()
