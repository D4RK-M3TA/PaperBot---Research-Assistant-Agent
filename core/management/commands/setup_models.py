"""
Management command to set up default embedding and generation models.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import EmbeddingModel, GenerationModel


class Command(BaseCommand):
    help = 'Set up default embedding and generation models'

    def handle(self, *args, **options):
        # Create default embedding model
        embedding_model, created = EmbeddingModel.objects.get_or_create(
            name='default',
            version='1.0',
            defaults={
                'model_path': settings.EMBEDDING_MODEL,
                'dimension': 384,  # all-MiniLM-L6-v2 dimension
                'description': 'Default sentence transformer model',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created embedding model: {embedding_model}')
            )
        else:
            self.stdout.write(f'Embedding model already exists: {embedding_model}')
        
        # Deactivate other embedding models
        EmbeddingModel.objects.exclude(id=embedding_model.id).update(is_active=False)
        
        # Create default generation models
        generation_models = [
            {
                'name': 'gpt-4',
                'version': '1.0',
                'provider': 'openai',
                'model_id': 'gpt-4',
                'description': 'OpenAI GPT-4',
                'is_active': True
            },
            {
                'name': 'gpt-3.5-turbo',
                'version': '1.0',
                'provider': 'openai',
                'model_id': 'gpt-3.5-turbo',
                'description': 'OpenAI GPT-3.5 Turbo',
                'is_active': False
            },
            {
                'name': 'claude-3-opus',
                'version': '1.0',
                'provider': 'anthropic',
                'model_id': 'claude-3-opus-20240229',
                'description': 'Anthropic Claude 3 Opus',
                'is_active': False
            },
        ]
        
        for model_data in generation_models:
            model, created = GenerationModel.objects.get_or_create(
                name=model_data['name'],
                version=model_data['version'],
                defaults=model_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created generation model: {model}')
                )
            else:
                self.stdout.write(f'Generation model already exists: {model}')
        
        # Activate first model if none is active
        if not GenerationModel.objects.filter(is_active=True).exists():
            first_model = GenerationModel.objects.first()
            if first_model:
                first_model.is_active = True
                first_model.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Activated generation model: {first_model}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Model setup completed successfully!')
        )



