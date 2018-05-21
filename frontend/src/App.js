import React from 'react';
import './App.css';
import {
  BrowserRouter as Router,
  Route,
} from 'react-router-dom'
import Login from './login'
import Logout from './logout'
import Home from './home'
import Navbar from './navbar'

const App = () => (
  <Router>
    <div>
      <Route path="" component={Navbar}/>
      <Route path="" component={Home}/>
      <Route path="/login" component={Login}/>
      <Route path="/logout" component={Logout}/>
    </div>
  </Router>
)

export default App;
