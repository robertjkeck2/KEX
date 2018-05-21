import * as actionType from './types';

export const setToken = (data) => {
  return {
    type: actionType.SET_TOKEN,
    data
  }
}

export const resetToken = (data) => {
  return {
    type: actionType.RESET_TOKEN,
    data
  }
}
