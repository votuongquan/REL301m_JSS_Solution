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
import FallingText from '../../components/animations/FallingText';

const meta = {
  title: 'Examples/Landing Page Section',
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'A complete landing page section showcasing multiple components working together.',
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

export const HeroSection: Story = {
  render: () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-8">
      <div className="max-w-4xl mx-auto text-center space-y-8">
        <FallingText variant="scale" delay={0}>
          <h1 className="text-6xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            EntervIU
          </h1>
        </FallingText>
        
        <FallingText variant="fade" delay={0.3}>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            The ultimate platform for conducting and managing interviews with AI-powered insights
          </p>
        </FallingText>

        <FallingText variant="bounce" delay={0.6}>
          <div className="flex gap-4 justify-center">
            <Button size="lg">Get Started</Button>
            <Button variant="outline" size="lg">Learn More</Button>
          </div>
        </FallingText>
      </div>
    </div>
  ),
};

export const FeaturesSection: Story = {
  render: () => (
    <div className="bg-white py-16 px-8">
      <div className="max-w-6xl mx-auto">
        <FallingText variant="fade" delay={0}>
          <h2 className="text-4xl font-bold text-center mb-12">
            Powerful Features
          </h2>
        </FallingText>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <FallingText variant="slide" delay={0.2}>
            <Card className="h-full">
              <CardHeader>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <span className="text-2xl">🎯</span>
                </div>
                <CardTitle>AI-Powered Analysis</CardTitle>
                <CardDescription>
                  Get intelligent insights from your interviews with advanced AI
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Our AI analyzes responses, body language, and speech patterns to provide comprehensive candidate evaluations.
                </p>
              </CardContent>
            </Card>
          </FallingText>

          <FallingText variant="slide" delay={0.4}>
            <Card className="h-full">
              <CardHeader>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                  <span className="text-2xl">💬</span>
                </div>
                <CardTitle>Real-time Chat</CardTitle>
                <CardDescription>
                  Seamless communication during interviews
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Built-in chat functionality allows for smooth communication and note-taking during the interview process.
                </p>
              </CardContent>
            </Card>
          </FallingText>

          <FallingText variant="slide" delay={0.6}>
            <Card className="h-full">
              <CardHeader>
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                  <span className="text-2xl">📊</span>
                </div>
                <CardTitle>Advanced Analytics</CardTitle>
                <CardDescription>
                  Detailed reports and analytics for better decisions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Comprehensive dashboards and reports help you make data-driven hiring decisions.
                </p>
              </CardContent>
            </Card>
          </FallingText>
        </div>
      </div>
    </div>
  ),
};

export const CTASection: Story = {
  render: () => (
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 py-16 px-8">
      <div className="max-w-4xl mx-auto text-center text-white space-y-6">
        <FallingText variant="scale" delay={0}>
          <h2 className="text-4xl font-bold">
            Ready to Transform Your Hiring Process?
          </h2>
        </FallingText>
        
        <FallingText variant="fade" delay={0.3}>
          <p className="text-xl opacity-90">
            Join thousands of companies already using EntervIU to find the perfect candidates
          </p>
        </FallingText>

        <FallingText variant="bounce" delay={0.6}>
          <div className="flex gap-4 justify-center">
            <Button size="lg" variant="secondary">
              Start Free Trial
            </Button>
            <Button size="lg" variant="outline" className="text-white border-white hover:bg-white hover:text-blue-600">
              Schedule Demo
            </Button>
          </div>
        </FallingText>
      </div>
    </div>
  ),
};