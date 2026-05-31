import { Button } from './Button.astro';

export default {
  title: 'Components/Button',
  component: Button,
  argTypes: {
    variant: { control: { type: 'select', options: ['primary', 'secondary', 'tertiary'] } },
    size: { control: { type: 'select', options: ['sm', 'md', 'lg'] } },
    disabled: { control: { type: 'boolean' } },
    type: { control: { type: 'select', options: ['submit', 'button', 'reset'] } },
  },
};

export const Primary = {
  args: {
    variant: 'primary',
    size: 'md',
    children: 'Primary Button',
  },
};

export const Secondary = {
  args: {
    variant: 'secondary',
    size: 'md',
    children: 'Secondary Button',
  },
};

export const Tertiary = {
  args: {
    variant: 'tertiary',
    size: 'md',
    children: 'Tertiary Button',
  },
};

export const Disabled = {
  args: {
    variant: 'primary',
    size: 'md',
    disabled: true,
    children: 'Disabled Button',
  },
};

export const Small = {
  args: {
    variant: 'primary',
    size: 'sm',
    children: 'Small Button',
  },
};

export const Large = {
  args: {
    variant: 'primary',
    size: 'lg',
    children: 'Large Button',
  },
};