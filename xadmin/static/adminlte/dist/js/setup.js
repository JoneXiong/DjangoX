  function store(name, val) {
    if (typeof (Storage) !== "undefined") {
      localStorage.setItem(name, val);
    } else {
      window.alert('Please use a modern browser to properly view this template!');
    }
  }

  function get(name) {
    if (typeof (Storage) !== "undefined") {
      return localStorage.getItem(name);
    } else {
      window.alert('Please use a modern browser to properly view this template!');
    }
  }


$(document).ready(function(){

  var AdminLTE = $.AdminLTE;
  var tmp = get('sidebar-collapse');

  function change_layout(cls) {
    $("body").toggleClass(cls);
  }

    $(".sidebar-toggle").on('click', function () {
        if (!$('body').hasClass('sidebar-collapse')) {
            store('sidebar-collapse','sidebar-collapse');
        }
        else{
            store('sidebar-collapse','');
        }
    });
    change_layout('fixed');
    if (tmp)change_layout('sidebar-collapse') 
});
