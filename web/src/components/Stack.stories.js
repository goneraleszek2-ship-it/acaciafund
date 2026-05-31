import { Stack } from './Stack.astro';

export default {
  title: 'Components/Stack',
  component: Stack,
  argTypes: {
    spacing: { control: { type: 'select', options: ['xs', 'sm', 'md', 'lg', 'xl', '2xl', '3xl', '4xl'] } },
    direction: { control: { type: 'select', options: ['vertical', 'horizontal'] } },
  },
};

export const Vertical = {
  args: {
    spacing: 'md',
    direction: 'vertical',
    children: [
      '<div style="background: var(--color-background-elevated); padding: var(--spacing-sm); border-radius: var(--radius-md);">Item 1</div>',
      '<div style="background: var(--color-background-elevated); padding: var(--spacing-sm); border-radius: var(--radius-md);">Item 2</div>',
      '<div style="background: var(--color-background-elevated); padding: var(--spacing-sm); border-radius: var(--radius-md);">Item 3</div>',
    ],
  },
};

export const Horizontal = {
  args: {
    spacing: 'sm',
    direction: 'horizontal',
    children: [
      '<div style="background: var(--color-background-elevated); padding: var(--spacing-xs); border-radius: var(--radius-sm);">Item A</div>',
      '<div style="background: var(--color-background-elevated); padding: var(--spacing-xs); border-radius: var(--radius-sm);">Item B</div>',
      '<div style="background: var(--color-background-elevated); padding: var(--spacing-xs); border-radius: var(--radius-sm);">Item C</div>',
    ],
  },
};

export const ReverseVertical = {
  args: {
    ...Vertical.args,
    direction: 'vertical',
    // Note: We don't have a reverse option in the component, but we can show how it would be done by changing the order of children.
    // For now, we just show the same as vertical but note that the component doesn't support reverse via a prop.
    // We can add a reverse prop if needed, but for the story we can just reverse the children manually.
    children: [
      '<div style="background: var(--color-background-elevated); padding: var(--spacing-sm); border-radius: var(--radius-md);">Item 3</div>',
      '<div style="background: var(--color-background-elevated); padding: var(--spacing-sm); border-radius: var(--radius-md);">Item 2</div>',
      '<div style="background: var(--color-background-elevated); padding: var(--spacing-sm); border-radius: var(--radius-md);">Item 1</div>',
    ],
  },
};