import type { Meta, StoryObj } from '@storybook/react';
import FallingText from '../../components/animations/FallingText';

const meta = {
  title: 'Animations/FallingText',
  component: FallingText,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'An animated text component that creates smooth entrance animations with various motion effects.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['default', 'smooth', 'bounce', 'slide', 'fade', 'scale'],
      description: 'The animation variant to use',
    },
    delay: {
      control: { type: 'number', min: 0, max: 2, step: 0.1 },
      description: 'Delay before animation starts (in seconds)',
    },
    duration: {
      control: { type: 'number', min: 0.1, max: 3, step: 0.1 },
      description: 'Duration of the animation (in seconds)',
    },
    className: {
      control: { type: 'text' },
      description: 'Additional CSS classes',
    },
  },
  args: {
    children: 'Animated Text',
    delay: 0,
    duration: 0.8,
    variant: 'default',
  },
} satisfies Meta<typeof FallingText>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: 'Welcome to our platform!',
    variant: 'default',
  },
};

export const Smooth: Story = {
  args: {
    children: 'Smooth animation variant',
    variant: 'smooth',
  },
};

export const Bounce: Story = {
  args: {
    children: 'Bouncy entrance!',
    variant: 'bounce',
  },
};

export const Slide: Story = {
  args: {
    children: 'Sliding from the side',
    variant: 'slide',
  },
};

export const Fade: Story = {
  args: {
    children: 'Fading into view',
    variant: 'fade',
  },
};

export const Scale: Story = {
  args: {
    children: 'Scaling up with rotation',
    variant: 'scale',
  },
};

export const WithDelay: Story = {
  args: {
    children: 'This text appears after 1 second',
    delay: 1,
    variant: 'bounce',
  },
};

export const SlowAnimation: Story = {
  args: {
    children: 'Very slow animation',
    duration: 2.5,
    variant: 'smooth',
  },
};

export const StyledHeading: Story = {
  args: {
    children: 'Beautiful Heading',
    variant: 'scale',
    className: 'text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent',
  },
};

export const MultipleTexts: Story = {
  render: () => (
    <div className="space-y-4 text-center">
      <FallingText variant="fade" delay={0}>
        <h1 className="text-3xl font-bold">Welcome</h1>
      </FallingText>
      <FallingText variant="slide" delay={0.3}>
        <h2 className="text-xl text-gray-600">to our amazing platform</h2>
      </FallingText>
      <FallingText variant="bounce" delay={0.6}>
        <p className="text-gray-500">Experience the magic of animations</p>
      </FallingText>
    </div>
  ),
};