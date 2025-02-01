import { useNavigate } from 'react-router-dom';

/**
 * Custom hook to handle navigation to the login page.
 */
export function useShowLogin() {
  const navigate = useNavigate();

  /**
   * Navigate to the login page.
   */
  function showLogin() {
    navigate('/login');
  }

  return { showLogin };
}
