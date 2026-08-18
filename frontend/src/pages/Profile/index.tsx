import { useState, useEffect } from "react";
import { profileApi } from "../../api";
import type { UserResponse } from "../../types";

export function ProfilePage() {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    profileApi
      .get()
      .then((data) => {
        setUser(data);
        setUsername(data.username);
        setEmail(data.email);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      const updated = await profileApi.update({ username, email });
      setUser(updated);
      setMessage("Profile updated!");
    } catch {
      setError("Failed to update profile");
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      await profileApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setMessage("Password changed!");
      setCurrentPassword("");
      setNewPassword("");
    } catch {
      setError("Failed to change password — check current password");
    }
  };

  if (loading) return <p>Loading profile...</p>;
  if (!user) return <p>Failed to load profile.</p>;

  return (
    <div className="profile-page">
      <h1>Profile</h1>
      <p className="role">
        Role: <strong>{user.role}</strong>
      </p>

      <form onSubmit={handleUpdateProfile} className="profile-form">
        <h3>Account Info</h3>
        <label>
          Username:
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>
        <label>
          Email:
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <button type="submit" className="btn btn--primary">
          Update Profile
        </button>
      </form>

      <form onSubmit={handleChangePassword} className="profile-form">
        <h3>Change Password</h3>
        <label>
          Current Password:
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
          />
        </label>
        <label>
          New Password:
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
        </label>
        <button type="submit" className="btn btn--primary">
          Change Password
        </button>
      </form>

      {message && <p className="success">{message}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
