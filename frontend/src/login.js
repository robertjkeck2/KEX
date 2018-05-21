import React, { Component } from 'react'
import { login } from './util/Auth.js'
import { Redirect } from 'react-router-dom'
import { store } from './store'

class Login extends Component {

  constructor(props) {
    super(props);
    this.state = {
        username: '',
        password: '',
        auth: false,
        invalidCred: null,
    };
    store.subscribe(() => {
      this.setState({
        auth: store.getState().token != null,
      });
    });
    this.logIn = this.logIn.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
  }

  logIn() {
    const self = this;
    login(this.state.username, this.state.password)
    .catch(function(error) {
      self.setState({invalidCred: true});
    });
  }

  handleInputChange(event) {
    const target = event.target;
    const value = target.value;
    const name = target.name;

    this.setState({
      [name]: value
    });
  }

  handleSubmit(event) {
    this.logIn()
    event.preventDefault();
  }

  render() {
    if (this.state.auth) {
     return <Redirect to='/'/>
    }
    var alert = {};
    if (this.state.invalidCred) {
      alert = (
        <p className="alert">Invalid credentials. Please try again</p>
      )
    } else {
      alert = (
        <p></p>
      )
    }
    return (
      <div className="login">
        <div className="loginscreen">
          <h1>Login</h1>
          <form onSubmit={this.handleSubmit}>
            <input type="text" name="username" placeholder="Username" onChange={this.handleInputChange}/>
            <input type="password" name="password" placeholder="Password" onChange={this.handleInputChange}/>
            <input className="btn" type="submit" value="Submit" />
          </form>
          {alert}
        </div>
      </div>
    )
  }
}

export default Login;
