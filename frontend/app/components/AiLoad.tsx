export default function LoadingScreen() {
    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-8 rounded-3xl">
            <div className="text-center max-w-md w-full">
                {/* Spinner */}
                <div className="w-16 h-16 mx-auto mb-8 border-4 border-gray-200 dark:border-gray-700 border-t-blue-500 dark:border-t-blue-400 rounded-full animate-spin"></div>
                
                {/* Text */}
                <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-2">
                    Finding Your Perfect Home
                </h1>
                <p className="text-base text-gray-600 dark:text-gray-300 mb-8">
                    Searching student properties
                </p>

                {/* Animated dots */}
                <div className="flex justify-center gap-2">
                    <div className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full animate-bounce [animation-delay:0s]"></div>
                    <div className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                    <div className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                </div>
            </div>
        </div>
    );
}