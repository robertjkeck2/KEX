import React, { Component } from 'react'
import { Link } from 'react-router-dom'
import { store } from './store'

class Navbar extends Component {

  constructor(props) {
    super(props);
    this.state = {
        auth: false,
    };
    store.subscribe(() => {
      this.setState({
        auth: store.getState().token != null,
      });
    });
  }

  render() {
    var links = {}
    if (this.state.auth) {
      links = (
        <div className="navbar">
          <div className="links">
            <Link to="/logout"><button className="btn">Logout</button></Link>&nbsp;
          </div>
        </div>
      )
    }
    else {
      links = (
        <div className="navbar">
          <div className="links">
            <Link to="/login"><button className="btn">Login</button></Link>&nbsp;
          </div>
        </div>
      )
    }
    return (
      <div>
        {links}
      </div>
    )
  }
}

export default Navbar;
