// pages/index.js

import Link from "next/link";
import { ChatBubbleLeftRightIcon } from "@heroicons/react/24/solid"; // Corrected import path

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 dark:from-gray-900 dark:to-gray-800 flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8 text-gray-800 dark:text-gray-100 transform animate-slideInLeft">
        <div className="flex flex-col items-center">
          <ChatBubbleLeftRightIcon className="h-16 w-16 text-primary mb-4 animate-bounce" />
          <h1 className="text-4xl font-extrabold mb-4 text-center text-primary dark:text-primary-dark animate-fadeIn">
            BUREASY
          </h1>
          <p className="text-center text-gray-700 dark:text-gray-300 mb-8 animate-fadeIn">
            Simplifying your bureaucratic tasks with ease.
          </p>

          <Link
            href="/dashboard"
            className="inline-flex items-center px-6 py-3 bg-primary text-white font-semibold rounded-md shadow hover:bg-primary-dark transition transform hover:scale-105"
          >
            <ChatBubbleLeftRightIcon className="h-5 w-5 mr-2 animate-pulseSlow" />
            Get Started
          </Link>
        </div>
      </div>
    </div>
  );
}
