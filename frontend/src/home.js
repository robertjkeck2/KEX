import React, { Component } from 'react'
import axios from 'axios';
import _ from 'lodash';
import { URL } from './config/Api';
import { InvalidCredentialsException } from './util/Auth'

class Home extends Component {

  constructor(props) {
    super(props);
    this.state = {
        best_ask: ''
    };
    this.checkPrice = this.checkPrice.bind(this);
  }

  checkPrice() {
    const self = this;
    axios.get(URL + '/api/price/', {
      created_at_0: '2018-05-15',
      created_at_1: '2018-05-18'
    })
    .then(function (response) {
      self.setState({best_ask: response.data[0].best_ask})}
    )
    .catch(function (error) {
      if (_.get(error, 'response.status') === 400) {
        throw new InvalidCredentialsException(error);
      }
      throw error;
    });
  }

  componentDidMount() {
    this.checkPrice();
  }

  render() {
    var prices = this.state.best_ask;
    return (
      <div>
        <h2>Home</h2>
        {prices}
      </div>
    )
  }
}

export default Home;
