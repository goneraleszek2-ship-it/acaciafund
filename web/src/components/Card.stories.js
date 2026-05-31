import { Card } from './Card.astro';

export default {
  title: 'Components/Card',
  component: Card,
  argTypes: {
    title: { control: 'text' },
    subtitle: { control: 'text' },
    image: { control: 'object' },
  },
};

export const Default = {
  args: {
    title: 'Card Title',
    subtitle: 'Card Subtitle',
    children: 'This is the content of the card.',
  },
};

export const WithImage = {
  args: {
    title: 'Card with Image',
    subtitle: 'This card has an image',
    image: {
      src: '/images/bayes.svg',
      alt: 'Bayesian reasoning illustration'
    },
    children: 'This is the content of the card with an image above it.',
  },
};

export const Elevated = {
  args: {
    title: 'Elevated Card',
    subtitle: 'With custom class for elevation',
    class: 'elevated-card',
    children: 'This card has custom styling applied via class.',
  },
};