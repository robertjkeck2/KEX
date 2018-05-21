import React, { Component } from 'react'
import { Redirect } from 'react-router-dom'
import { store, persistor } from './store'
import { resetToken } from './actions'

class Logout extends Component {

  constructor(props) {
      super(props);
      this.logOut = this.logOut.bind(this);
  }

  logOut() {
    store.dispatch(resetToken(null));
    persistor.purge();
  }

  componentWillMount() {
    this.logOut();
  }

  render() {
    return (
      <Redirect to="/" />
    )
  }
}

export default Logout;
