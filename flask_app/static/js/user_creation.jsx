import React from 'react';
import ReactDOM from 'react-dom/client';
import UserCreationForm from './react/UserCreationForm';

const root = ReactDOM.createRoot(document.getElementById('user-creation-root'));
root.render(
  <React.StrictMode>
    <UserCreationForm config={window.userCreationConfig} />
  </React.StrictMode>
);