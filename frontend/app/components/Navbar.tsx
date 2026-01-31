import React from "react";
import { FaInstagram, FaTiktok } from "react-icons/fa";
import { Link } from "react-router";

export function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur border-b border-gray-200 dark:bg-gray-900/90 dark:border-gray-800">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link to={"/"} className="text-xl font-bold text-gray-900 dark:text-gray-100">studentHomes</Link>
        </div>

        <div className="flex items-center gap-4">
          <Link to={"/signin"} className="text-sm px-3 py-1 rounded-md">Sign in</Link>
          <Link to={"/signup"} className="text-sm px-3 py-1 rounded-md border border-gray-200 dark:border-gray-700">Sign up</Link>
          <a href="#" aria-label="Instagram" className="text-gray-600 hover:text-gray-900 dark:text-gray-300">
            <FaInstagram size={18} />
          </a>
          <a href="#" aria-label="TikTok" className="text-gray-600 hover:text-gray-900 dark:text-gray-300">
            <FaTiktok size={18} />
          </a>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
