import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import Recommendations from '../src/pages/Recommendations';
import { apiClient } from '../src/api/client';

vi.mock('../src/api/client', async () => {
  const actual = await vi.importActual<typeof import('../src/api/client')>('../src/api/client');
  return {
    ...actual,
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
    },
  };
});

// Matches the actual backend shape: { recommendations: [{ mealId, score, breakdown, meal }] }
const mockMeal = {
  id: 'meal-1',
  name: 'Wild Salmon Quinoa Bowl',
  restaurant: 'Green Kitchen',
  cuisine: 'Healthy',
  mealType: 'LUNCH',
  calories: 450,
  proteinG: 45,
  carbsG: 30,
  fatG: 12,
  price: 18,
  platform: 'SWIGGY',
  healthScore: 80,
  isVegetarian: false,
  isVegan: false,
  allergens: [],
  imageUrl: 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80',
  deepLinkQuery: 'Wild Salmon Quinoa Bowl',
};

const mockRecommendationItem = {
  mealId: 'meal-1',
  score: 98,
  breakdown: { calorieAccuracy: 95, proteinQuality: 99, budgetFit: 90, healthScore: 85 },
  meal: mockMeal,
};

const mockApiResponse = {
  data: { recommendations: [mockRecommendationItem] },
};

describe('Recommendations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.open = vi.fn();
  });

  it('renders meal cards with key nutrition info', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce(mockApiResponse);

    render(
      <MemoryRouter>
        <Recommendations />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('Wild Salmon Quinoa Bowl')).toBeInTheDocument();
    });
    expect(screen.getByText('450 kcal')).toBeInTheDocument();
    expect(screen.getByText('45g Protein')).toBeInTheDocument();
  });

  it('renders the meal image when imageUrl is present', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce(mockApiResponse);

    render(
      <MemoryRouter>
        <Recommendations />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('Wild Salmon Quinoa Bowl')).toBeInTheDocument();
    });

    const img = screen.getByAltText('Wild Salmon Quinoa Bowl') as HTMLImageElement;
    expect(img).toBeInTheDocument();
    expect(img.src).toContain('unsplash.com');
  });

  it('shows the fallback icon when imageUrl is missing', async () => {
    const noImage = {
      data: {
        recommendations: [
          { ...mockRecommendationItem, meal: { ...mockMeal, imageUrl: undefined } },
        ],
      },
    };
    vi.mocked(apiClient.get).mockResolvedValueOnce(noImage);

    render(
      <MemoryRouter>
        <Recommendations />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('Wild Salmon Quinoa Bowl')).toBeInTheDocument();
    });

    // No img element should be rendered when imageUrl is absent
    expect(screen.queryByAltText('Wild Salmon Quinoa Bowl')).toBeNull();
  });

  it('calls the orders API with the right payload when ordering', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce(mockApiResponse);
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: {
        order: { id: 'order-1', platform: 'SWIGGY', status: 'REDIRECTED', userId: 'u1', mealId: 'meal-1', createdAt: '' },
        deepLink: 'https://www.swiggy.com/search?query=Wild+Salmon+Quinoa+Bowl',
      },
    });

    render(
      <MemoryRouter>
        <Recommendations />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('Wild Salmon Quinoa Bowl')).toBeInTheDocument();
    });

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /order on swiggy/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/api/orders', {
        mealId: 'meal-1',
        platform: 'SWIGGY',
      });
    });
  });
});
