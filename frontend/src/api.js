import axios from 'axios'

const API = axios.create({
  baseURL: 'http://localhost:5000/api',
  withCredentials: true  // send session cookie with every request
})

API.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) router.push('/login')
    return Promise.reject(err)
  }
)


export default API
