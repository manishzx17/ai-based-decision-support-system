import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Lock, Mail, ArrowRight, ShieldCheck } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('patient@example.com');
  const [password, setPassword] = useState('demo1234');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // Quick client sign in
    localStorage.setItem('user_token', 'demo_token_123');
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full glass-card p-8 rounded-3xl border border-slate-200 shadow-xl">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-2xl gradient-bg flex items-center justify-center text-white font-black text-2xl mx-auto mb-3 shadow-md">
            12C
          </div>
          <h2 className="text-2xl font-black text-slate-900">Sign in to 12C Medical System</h2>
          <p className="text-xs text-slate-500 mt-1">Access your medical reports, travel plans, and AI assistant</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500 focus:outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-3 rounded-xl font-bold text-xs text-white gradient-bg shadow-md hover:opacity-95 transition-all flex items-center justify-center gap-2 mt-4"
          >
            <span>Sign In</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-500">
          Don't have an account?{' '}
          <Link to="/register" className="text-sky-600 font-bold hover:underline">
            Register as New Patient
          </Link>
        </div>
      </div>
    </div>
  );
};
