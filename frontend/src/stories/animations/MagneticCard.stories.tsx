import type { Meta, StoryObj } from '@storybook/react';
import MagneticCard from '../../components/animations/MagneticCard';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';

const meta = {
  title: 'Animations/MagneticCard',
  component: MagneticCard,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A card component that follows the mouse cursor with a magnetic effect, creating an engaging interactive experience.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    strength: {
      control: { type: 'range', min: 5, max: 50, step: 5 },
      description: 'Intensity of the magnetic effect',
    },
    className: {
      control: { type: 'text' },
      description: 'Additional CSS classes',
    },
  },
  args: {
    strength: 20,
  },
} satisfies Meta<typeof MagneticCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: (args) => (
    <MagneticCard {...args}>
      <Card className="w-[300px] cursor-pointer">
        <CardHeader>
          <CardTitle>Magnetic Card</CardTitle>
          <CardDescription>Hover to see the magnetic effect</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Move your cursor around this card to see it follow your mouse!</p>
        </CardContent>
      </Card>
    </MagneticCard>
  ),
};

export const StrongMagnetism: Story = {
  args: {
    strength: 40,
  },
  render: (args) => (
    <MagneticCard {...args}>
      <Card className="w-[300px] cursor-pointer bg-gradient-to-br from-purple-500 to-pink-500 text-white">
        <CardHeader>
          <CardTitle>Strong Magnetic Effect</CardTitle>
          <CardDescription className="text-purple-100">Very responsive to mouse movement</CardDescription>
        </CardHeader>
        <CardContent>
          <p>This card has a much stronger magnetic effect!</p>
        </CardContent>
      </Card>
    </MagneticCard>
  ),
};

export const SubtleMagnetism: Story = {
  args: {
    strength: 8,
  },
  render: (args) => (
    <MagneticCard {...args}>
      <Card className="w-[300px] cursor-pointer">
        <CardHeader>
          <CardTitle>Subtle Effect</CardTitle>
          <CardDescription>Gentle magnetic interaction</CardDescription>
        </CardHeader>
        <CardContent>
          <p>This card has a very subtle magnetic effect for a more professional feel.</p>
        </CardContent>
      </Card>
    </MagneticCard>
  ),
};

export const ProductCard: Story = {
  args: {
    strength: 25,
  },
  render: (args) => (
    <MagneticCard {...args}>
      <Card className="w-[280px] cursor-pointer overflow-hidden">
        <div className="h-40 bg-gradient-to-br from-blue-400 to-purple-600"></div>
        <CardHeader>
          <CardTitle>Premium Product</CardTitle>
          <CardDescription>$99.99</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600">High-quality product with amazing features that will exceed your expectations.</p>
          <Button className="w-full mt-4">Add to Cart</Button>
        </CardContent>
      </Card>
    </MagneticCard>
  ),
};

export const TeamMemberCard: Story = {
  args: {
    strength: 15,
  },
  render: (args) => (
    <MagneticCard {...args}>
      <Card className="w-[250px] cursor-pointer text-center">
        <CardHeader>
          <div className="w-20 h-20 bg-gradient-to-br from-green-400 to-blue-500 rounded-full mx-auto mb-4"></div>
          <CardTitle>Sarah Johnson</CardTitle>
          <CardDescription>Lead Developer</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600">Passionate about creating amazing user experiences with modern technologies.</p>
          <div className="flex justify-center space-x-2 mt-4">
            <Button variant="outline" size="sm">LinkedIn</Button>
            <Button variant="outline" size="sm">GitHub</Button>
          </div>
        </CardContent>
      </Card>
    </MagneticCard>
  ),
};

export const MultipleCards: Story = {
  render: () => (
    <div className="grid grid-cols-2 gap-6">
      <MagneticCard strength={20}>
        <Card className="cursor-pointer">
          <CardHeader>
            <CardTitle>Card 1</CardTitle>
            <CardDescription>First magnetic card</CardDescription>
          </CardHeader>
          <CardContent>
            <p>This is the first card in a grid layout.</p>
          </CardContent>
        </Card>
      </MagneticCard>
      
      <MagneticCard strength={20}>
        <Card className="cursor-pointer">
          <CardHeader>
            <CardTitle>Card 2</CardTitle>
            <CardDescription>Second magnetic card</CardDescription>
          </CardHeader>
          <CardContent>
            <p>This is the second card in a grid layout.</p>
          </CardContent>
        </Card>
      </MagneticCard>
      
      <MagneticCard strength={20}>
        <Card className="cursor-pointer">
          <CardHeader>
            <CardTitle>Card 3</CardTitle>
            <CardDescription>Third magnetic card</CardDescription>
          </CardHeader>
          <CardContent>
            <p>This is the third card in a grid layout.</p>
          </CardContent>
        </Card>
      </MagneticCard>
      
      <MagneticCard strength={20}>
        <Card className="cursor-pointer">
          <CardHeader>
            <CardTitle>Card 4</CardTitle>
            <CardDescription>Fourth magnetic card</CardDescription>
          </CardHeader>
          <CardContent>
            <p>This is the fourth card in a grid layout.</p>
          </CardContent>
        </Card>
      </MagneticCard>
    </div>
  ),
};