import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

// Your Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyCkPitiJXXU4P2XuaOo5sA8wY8_ZyPcU7A",
    authDomain: "geospatial-ai-b9bb9.firebaseapp.com",
    projectId: "geospatial-ai-b9bb9",
    storageBucket: "geospatial-ai-b9bb9.firebasestorage.app",
    messagingSenderId: "769076744494",
    appId: "1:769076744494:web:affcf9b96e34e3b1df6abf",
    // measurementId: "G-EXDGF5DGPM"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

export { auth, provider };