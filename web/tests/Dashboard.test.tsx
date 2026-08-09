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

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders calorie and macro targets when a profile exists', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        calorieTarget: 2400,
        proteinTargetG: 180,
        carbTargetG: 250,
        fatTargetG: 70,
        bmiCategory: 'Normal weight',
        bmi: 22.5,
        bmr: 1600,
        tdee: 2350,
      },
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('2400')).toBeInTheDocument();
    });
    expect(screen.getByText('Normal weight')).toBeInTheDocument();
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
