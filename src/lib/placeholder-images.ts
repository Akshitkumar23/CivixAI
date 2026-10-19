export type ImagePlaceholder = {
  id: string;
  description: string;
  imageUrl: string;
  imageHint: string;
};

const data = {
  "placeholderImages": [
    {
      "id": "hero-image",
      "description": "A diverse group of Indian citizens smiling.",
      "imageUrl": "https://picsum.photos/seed/1/600/400",
      "imageHint": "indian people"
    },
    {
      "id": "landing-hero",
      "description": "An AI bot assisting a family with civic services in front of government buildings.",
      "imageUrl": "https://picsum.photos/seed/11/600/400",
      "imageHint": "AI government"
    },
    {
      "id": "location-map",
      "description": "A technological representation of a map.",
      "imageUrl": "https://picsum.photos/seed/2/600/500",
      "imageHint": "map technology"
    }
  ]
};


export const PlaceHolderImages: ImagePlaceholder[] = data.placeholderImages;
