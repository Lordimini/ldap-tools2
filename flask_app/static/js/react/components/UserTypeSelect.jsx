import React from 'react';

function UserTypeSelect({ choices, value, onChange }) {
  return (
    <div className="mb-3">
      <label htmlFor="user_type" className="form-label">User Type:</label>
      <select 
        id="user_type" 
        className="form-select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">Select a user type</option>
        {choices.map((choice) => (
          <option key={choice[0]} value={choice[0]}>
            {choice[1]}
          </option>
        ))}
      </select>
    </div>
  );
}

export default UserTypeSelect;