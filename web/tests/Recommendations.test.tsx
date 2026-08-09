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

const mockMeal = {
  id: 'meal-1',
  name: 'Wild Salmon Quinoa Bowl',
  restaurant: 'Green Kitchen',
  cuisine: 'Healthy',
  calories: 450,
  proteinG: 45,
  carbsG: 30,
  fatG: 12,
  price: 18,
  platform: 'SWIGGY',
  matchScore: 98,
};

describe('Recommendations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.open = vi.fn();
  });

  it('renders meal cards with key nutrition info', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [mockMeal] });

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

  it('calls the orders API with the right payload when ordering', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [mockMeal] });
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: { id: 'order-1', deepLink: 'https://swiggy.com/search', platform: 'SWIGGY' },
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
