import React from 'react';
import {
  Redirect,
  Route,
} from 'react-router-dom'
import { loggedIn } from './util/Auth'

export const ProtectedRoute =  ({ ...props }) => {
    const isAllowed = loggedIn();
    return isAllowed
        ? (<Route {...props} />)
        : (<Redirect to="/login" />)
};
