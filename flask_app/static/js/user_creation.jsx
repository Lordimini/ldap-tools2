// Sans imports ES6, utilisez directement les objets globaux
const root = ReactDOM.createRoot(document.getElementById('user-creation-root'));
root.render(
  React.createElement(UserCreationForm, {config: window.userCreationConfig})
);