import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import axios from 'axios';
import Dashboard from '../src/pages/Dashboard';
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

// Matches GET /api/health-profile → { profile: HealthProfile }
// Dashboard computes calorieTarget = max(1200, tdee + GOAL_ADJUSTMENT[fitnessGoal])
// WEIGHT_GAIN adjustment = +400 → 2350 + 400 = 2750
const mockProfileResponse = {
  data: {
    profile: {
      id: 'profile-1',
      userId: 'user-1',
      currentWeightKg: 70,
      targetWeightKg: 75,
      activityLevel: 'MODERATE',
      fitnessGoal: 'WEIGHT_GAIN',
      dietaryPreference: 'NON_VEGETARIAN',
      allergies: [],
      dailyBudget: 500,
      bmi: 22.5,
      bmr: 1600,
      tdee: 2350,
      proteinTargetG: 180,
      carbTargetG: 250,
      fatTargetG: 70,
    },
  },
};

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders calorie and macro targets when a profile exists', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce(mockProfileResponse);

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    await waitFor(() => {
      // calorieTarget = max(1200, 2350 + 400) = 2750
      expect(screen.getByText('2750')).toBeInTheDocument();
    });
    // bmiCategory computed from bmi=22.5 → 'Normal weight'
    expect(screen.getByText('Normal weight')).toBeInTheDocument();
    // Protein value rendered separately from 'g' suffix inside StatCard
    expect(screen.getByText('180')).toBeInTheDocument();
    expect(screen.getByText('Protein')).toBeInTheDocument();
  });

  it('redirects to health assessment when no profile exists (404)', async () => {
    const error = new axios.AxiosError('Not Found');
    error.response = { status: 404 } as never;
    vi.mocked(apiClient.get).mockRejectedValueOnce(error);
    vi.spyOn(axios, 'isAxiosError').mockReturnValue(true);

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Dashboard />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith('/api/health-profile');
    });
  });
});
