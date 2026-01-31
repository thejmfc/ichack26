import torch
import open_clip
from PIL import Image

class Embedder:
    def __init__(self, model_name='ViT-B-32', pretrained='laion2b_s34b_b79k', device=None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(model_name, pretrained=pretrained)
        self.model = self.model.to(self.device)
        self.tokenizer = open_clip.get_tokenizer(model_name)

    def embed_text(self, text: str):
        text_tokens = self.tokenizer([text]).to(self.device)
        with torch.no_grad():
            text_features = self.model.encode_text(text_tokens)
        return text_features

    def embed_image(self, image_path: str):
        image = Image.open(image_path).convert('RGB')
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
        return image_features

    @staticmethod
    def cosine_similarity(embedding1, embedding2):
        embedding1 = embedding1 / embedding1.norm(dim=-1, keepdim=True)
        embedding2 = embedding2 / embedding2.norm(dim=-1, keepdim=True)
        similarity = (embedding1 @ embedding2.T).item()
        return round(similarity * 100, 2)

    def similarity_image_text(self, image_embedding, text_embedding):
        return self.cosine_similarity(image_embedding, text_embedding)

    def similarity_text_text(self, text_embedding_one, text_embedding_two):
        return self.cosine_similarity(text_embedding_one, text_embedding_two)

    def similarity_image_image(self, image_embedding_one, image_embedding_two):
        return self.cosine_similarity(image_embedding_one, image_embedding_two)