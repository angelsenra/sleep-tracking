console.log("Hi console!");

// Get a url and call callback with the request object
function httpGet(url, callback) {
  var r = new XMLHttpRequest();
  r.open("GET", url, true);
  r.send();
  r.onreadystatechange = () => {
    if (r.readyState != 4)  // DONE
      return;
    callback(r);
  }
}

// Versbosely check status and return text
function xGet(r) {
  if (r.status == 200) {
    console.log("Succesfully loaded " + r.responseURL);
    return r.responseText;
  } else {
    console.log("Error loading " + r.responseURL);
    console.log("Status " + r.status + ": " + r.statusText);
  }

}

// Insert the content from url into element with id
function insertGet(url, id) {
  httpGet(url, r => {
    var text = xGet(r);
    if (text)
      document.getElementById(id).innerHTML = text;
  })
}

// Check if we are at the proper domain (Used not to confuse local tests)
// TODO: Should be removed in production
setTimeout(
  () => {
    var header = document.getElementById("header");
    if (location.hostname != "yadkee.herokuapp.com")
      header.style.textDecoration = "line-through";
    else {
      header.style.textDecoration = "none";
      header.style.color = "var(--color2)";
    }
    console.log("Successfully marked the header");
  }, 0)