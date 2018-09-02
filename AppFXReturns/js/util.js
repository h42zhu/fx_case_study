

function getCSRFToken() {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const xsrfCookies = document.cookie.split(';')
      .map(c => c.trim())
      .filter(c => c.startsWith('csrftoken='));

    if (xsrfCookies.length === 0) {
      return null;
    }
    cookieValue = decodeURIComponent(xsrfCookies[0].split('=')[1]);
  }
  return cookieValue;
}

export { getCSRFToken }