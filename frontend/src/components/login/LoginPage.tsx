import { Link } from 'react-router-dom';
import { auth, provider } from './firebaseConfigs';
import { signInWithPopup } from 'firebase/auth';

export function LoginPage() {
  const handleGoogleSignIn = () => {
    signInWithPopup(auth, provider)
      .then((result) => {
        // Handle successful sign-in
        console.log(result.user);
      })
      .catch((error) => {
        // Handle errors
        console.error(error);
      });
  };

  return (
    <>
      <nav className="absolute top-0 left-0 w-full flex justify-between items-center px-6 py-4 z-30">
        <div className="text-black text-lg font-semibold">
          <Link to="/" className="rounded-lg px-4 py-2 text-lg font-semibold text-black bg-gray-300 hover:bg-gray-300 transition-colors">
            Altara Geospatial AI
          </Link>
        </div>
        <div>
          <Link
            to="/signup"
            className="rounded-lg px-4 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 transition-colors duration-200"
          >
            Sign Up
          </Link>
        </div>
      </nav>
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white shadow-lg rounded-lg p-8 max-w-md w-full">
          <h1 className="text-2xl font-bold text-gray-900 text-center">Login</h1>
          <form className="mt-6">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter your email"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <input
                type="password"
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter your password"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-500 transition-colors duration-200"
            >
              Login
            </button>
          </form>
          <button
            onClick={handleGoogleSignIn}
            className="mt-4 w-full flex justify-center items-center px-4 py-2 text-sm font-semibold text-white bg-red-600 hover:bg-red-500 transition-colors duration-200 rounded-lg"
          >
            Sign in with Google
          </button>
          <div>
            <p className="mt-4 text-center">
              Don't have a username and password?
            </p>
            <Link to="/signup" className="text-blue-600 hover:text-blue-500 block text-center">
              Create an account
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}
