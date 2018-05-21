import { combineReducers } from 'redux';
import * as actionType from '../actions/types';
import storage from 'redux-persist/lib/storage'

const tokenInitialState = null;
const token = (state = tokenInitialState, action) => {
  switch(action.type) {
    case actionType.SET_TOKEN:
      return action.data;
    default:
      return state;
  }
}

const appReducer = combineReducers({
  token,
})

const rootReducer = (state, action) => {
  if (action.type === actionType.RESET_TOKEN) {
    state = undefined;
    storage.removeItem('persist:root')
  }
  return appReducer(state, action);
}

export default rootReducer;
