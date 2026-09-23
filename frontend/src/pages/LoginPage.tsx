import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, User, ArrowRight, ShieldCheck, Heart, AlertCircle, Activity, Brain, Bone } from 'lucide-react';
import { loginApi, getDemoUsersApi, DemoUserOption, SYNTHETIC_DEMO_USERS } from '../services/api';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('demo_cardio');
  const [password, setPassword] = useState('DemoPassword@123');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [demoUsers, setDemoUsers] = useState<DemoUserOption[]>(SYNTHETIC_DEMO_USERS);

  useEffect(() => {
    getDemoUsersApi().then((users) => {
      if (users && users.length > 0) {
        setDemoUsers(users);
      }
    });
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await loginApi(username, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err?.message || 'Invalid username or password. Please select a demo patient.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDemoUser = (user: DemoUserOption) => {
    setUsername(user.username);
    setPassword('DemoPassword@123');
    setError(null);
  };

  const getSpecialtyIcon = (specialty: string) => {
    switch (specialty.toLowerCase()) {
      case 'cardiology':
        return <Activity className="w-4 h-4 text-rose-500" />;
      case 'neurology':
        return <Brain className="w-4 h-4 text-purple-500" />;
      case 'orthopedics':
        return <Bone className="w-4 h-4 text-amber-500" />;
      default:
        return <Heart className="w-4 h-4 text-sky-500" />;
    }
  };

  return (
    <div className="min-h-[calc(100vh-10rem)] flex flex-col justify-center py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-xl w-full mx-auto space-y-6">
        
        {/* Header Branding */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-sky-100 text-sky-800 text-xs font-bold rounded-full">
            <ShieldCheck className="w-3.5 h-3.5 text-sky-600" />
            <span>Synthetic Patient Demo Session</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            AI Based Decision Support System
          </h1>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Select one of the 3 pre-configured synthetic demo patient accounts below to evaluate isolated clinical workflows.
          </p>
        </div>

        {/* 3 Selectable Synthetic Demo Patients */}
        <div className="space-y-2">
          <p className="text-xs font-bold text-slate-700 uppercase tracking-wider text-center">
            Select Synthetic Demo Patient
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            {demoUsers.map((u) => {
              const isSelected = username === u.username || username === u.email;
              return (
                <button
                  key={u.id}
                  type="button"
                  onClick={() => handleSelectDemoUser(u)}
                  className={`p-3 rounded-2xl border text-left transition-all relative ${
                    isSelected
                      ? 'bg-sky-50 border-sky-400 shadow-sm ring-2 ring-sky-300'
                      : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-1.5">
                      {getSpecialtyIcon(u.specialty)}
                      <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-700">
                        {u.specialty}
                      </span>
                    </div>
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                      ID: {u.id}
                    </span>
                  </div>
                  <p className="text-xs font-bold text-slate-900 truncate">{u.full_name}</p>
                  <p className="text-[10px] text-slate-500 truncate mt-0.5">{u.clinical_focus}</p>
                  <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px]">
                    <span className="font-mono text-slate-500">@{u.username}</span>
                    <span className="text-sky-600 font-semibold">{u.city}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Login Form */}
        <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-lg space-y-5 bg-white">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs font-medium flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Demo Username or Email
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. demo_cardio"
                  required
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="DemoPassword@123"
                  required
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500 focus:outline-none"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl font-bold text-xs text-white gradient-bg shadow-md hover:opacity-95 transition-all flex items-center justify-center gap-2 mt-2 disabled:opacity-60"
            >
              {loading ? (
                <span>Authenticating Patient Session...</span>
              ) : (
                <>
                  <span>Sign In as {username}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Demonstration Notice */}
          <div className="pt-4 border-t border-slate-100 text-[11px] text-slate-500 space-y-1 text-center">
            <p className="font-semibold text-slate-600">Synthetic Demo Environment</p>
            <p>
              Default demo password for all accounts: <code className="bg-slate-100 px-1.5 py-0.5 rounded font-mono text-slate-700">DemoPassword@123</code>
            </p>
            <p className="text-[10px] text-slate-400">
              Zero real patient data is stored. Each synthetic account isolates clinical findings and records.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
};

export default LoginPage;
