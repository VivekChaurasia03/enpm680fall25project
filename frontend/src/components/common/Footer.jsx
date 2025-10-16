const Footer = () => {
  return (
    <footer className="bg-gray-800 text-white mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-sm">
              © {new Date().getFullYear()} FleetWise. All rights reserved.
            </p>
          </div>
          <div className="flex space-x-6">
            <a href="#" className="text-sm hover:text-indigo-400 transition">
              About
            </a>
            <a href="#" className="text-sm hover:text-indigo-400 transition">
              Privacy
            </a>
            <a href="#" className="text-sm hover:text-indigo-400 transition">
              Terms
            </a>
            <a href="#" className="text-sm hover:text-indigo-400 transition">
              Contact
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;