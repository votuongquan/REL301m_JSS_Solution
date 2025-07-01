import type { Meta, StoryObj } from '@storybook/react';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter 
} from '../../components/ui/card';
import { Button } from '../../components/ui/button';

const meta = {
  title: 'UI/Card',
  component: Card,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A flexible card component with header, content, and footer sections.',
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card description goes here</CardDescription>
      </CardHeader>
      <CardContent>
        <p>This is the main content of the card. You can put any content here.</p>
      </CardContent>
    </Card>
  ),
};

export const WithFooter: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Create Account</CardTitle>
        <CardDescription>Enter your details to create a new account</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Email</label>
            <input 
              type="email" 
              placeholder="Enter your email"
              className="w-full p-2 border border-gray-300 rounded-md mt-1"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Password</label>
            <input 
              type="password" 
              placeholder="Enter your password"
              className="w-full p-2 border border-gray-300 rounded-md mt-1"
            />
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline">Cancel</Button>
        <Button>Create Account</Button>
      </CardFooter>
    </Card>
  ),
};

export const ProductCard: Story = {
  render: () => (
    <Card className="w-[300px]">
      <CardHeader>
        <div className="w-full h-48 bg-gradient-to-br from-blue-400 to-purple-500 rounded-t-lg mb-4"></div>
        <CardTitle>Premium Plan</CardTitle>
        <CardDescription>Perfect for growing businesses</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="text-3xl font-bold">$29<span className="text-lg font-normal">/month</span></div>
          <ul className="space-y-1 text-sm">
            <li>✅ Unlimited projects</li>
            <li>✅ Priority support</li>
            <li>✅ Advanced analytics</li>
            <li>✅ Custom integrations</li>
          </ul>
        </div>
      </CardContent>
      <CardFooter>
        <Button className="w-full">Get Started</Button>
      </CardFooter>
    </Card>
  ),
};

export const Minimal: Story = {
  render: () => (
    <Card className="w-[250px]">
      <CardContent className="p-6">
        <p className="text-center text-gray-600">
          Simple card with just content
        </p>
      </CardContent>
    </Card>
  ),
};

export const WithImage: Story = {
  render: () => (
    <Card className="w-[350px] overflow-hidden">
      <div className="h-48 bg-gradient-to-r from-pink-400 via-purple-500 to-indigo-500"></div>
      <CardHeader>
        <CardTitle>Beautiful Gradient</CardTitle>
        <CardDescription>A card with an image header</CardDescription>
      </CardHeader>
      <CardContent>
        <p>This card demonstrates how to use cards with image headers for more visual appeal.</p>
      </CardContent>
      <CardFooter>
        <Button variant="outline" className="w-full">Learn More</Button>
      </CardFooter>
    </Card>
  ),
};