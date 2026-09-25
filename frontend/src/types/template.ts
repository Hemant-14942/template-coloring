export interface ColorSet {
  dark: string;
  main: string;
  bright: string;
}

export interface Slide {
  number: number;
  name: string;
  change: string;
  recolor: boolean;
  preview_url: string;
  mask_url: string;
}

export interface TemplateDetail {
  id: string;
  name: string;
  base_colors: ColorSet;
  slides: Slide[];
}
