<!doctype html>
<html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      {% if title %}
      <title>{{ title }} - OrangeBook</title>
      {% else %}
      <title>Welcome to OrangeBook</title>
      {% endif %}
      <link
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
        rel="stylesheet"
        integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN"
        crossorigin="anonymous">
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        <link rel="stylesheet" href="../static/css/style.css">
    </head>
    <body>
	    <nav class="navbar navbar-expand-lg navbar-light bg-light">
        <div class="container-fluid">
          <a class="navbar-brand" href="{{ url_for('index') }}">OrangeBook</a>
          <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
          </button>
          <div class="collapse navbar-collapse" id="navbarSupportedContent">
            <ul class="navbar-nav me-auto mb-2 mb-lg-0">
              <li class="nav-item">
                <a class="nav-link" aria-current="page" href="{{ url_for('index') }}">Home</a>
              </li>
              <li class="nav-item">
                <a class="nav-link" aria-current="page" href="{{ url_for('explore') }}">Explore</a>
              </li>
            </ul>
	          {% if g.search_form %}
                <form class="navbar-form navbar-left" method="get"
                        action="{{ url_for('search') }}">
                    <div class="form-group">
                        {{ g.search_form.q(size=20, class='form-control',
                            placeholder=g.search_form.q.label.text) }}
                    </div>
                </form>
            {% endif %}
            <ul class="navbar-nav mb-2 mb-lg-0">
              {% if current_user.is_anonymous %}
              <li class="nav-item">
                <a class="nav-link" aria-current="page" href="{{ url_for('login') }}">Login</a>
              </li>
              {% else %}
	      <li class="nav-item">
              <a class="nav-link" aria-current="page" href="{{ url_for('messages') }}">{{ _('Messages') }}
                {% set unread_message_count = current_user.unread_message_count() %}
                <span id="message_count" class="badge text-bg-danger"
                      style="visibility: {% if unread_message_count %}visible
                                         {% else %}hidden{% endif %};">
                    {{ unread_message_count }}
                </span>
              </a>
            </li>
              <li class="nav-item">
                <a class="nav-link" aria-current="page" href="{{ url_for('user', username=current_user.username) }}">Profile</a>
              </li>
              <li class="nav-item">
                <a class="nav-link" aria-current="page" href="{{ url_for('logout') }}">Logout</a>
              </li>
              {% endif %}
            </ul>
          </div>
        </div>
      </nav>
      <div class="menu">
        <a href="#" class="menu-item highlight">Recomandation</a>
        <a href="#" class="menu-item">Fashion</a>
        <a href="#" class="menu-item">Food</a>
        <a href="#" class="menu-item">Makeup</a>
        <a href="#" class="menu-item">Movies</a>
        <a href="#" class="menu-item">Career</a>
        <a href="#" class="menu-item">Home Decoration</a>
        <a href="#" class="menu-item">Games</a>
        <a href="#" class="menu-item">Travel</a>
        <a href="#" class="menu-item">Fitness</a>
    </div>
    <script src="https://kit.fontawesome.com/a076d05399.js"></script>
      <div class="container mt-3">
        {% with messages = get_flashed_messages() %}
        {% if messages %}
          {% for message in messages %}
          <div class="alert alert-info" role="alert">{{ message }}</div>
          {% endfor %}
        {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
      </div>
      <script
          src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
          integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL"
          crossorigin="anonymous">
      </script>
      {{ moment.include_moment() }}
      <script>
	      function set_message_count(n) {
     		 const count = document.getElementById('message_count');
      		 count.innerText = n;
      		 count.style.visibility = n ? 'visible' : 'hidden';
    		}
      </script>
      {% block scripts %}
  	<script>
    	{% if current_user.is_authenticated %}
    	function initialize_notifications() {
      		let since = 0;
      		setInterval(async function() {
        		const response = await fetch('{{ url_for('notifications') }}?since=' + since);
        		const notifications = await response.json();
        		for (let i = 0; i < notifications.length; i++) {
          		if (notifications[i].name == 'unread_message_count')
            		set_message_count(notifications[i].data);
          		since = notifications[i].timestamp;
        		}
      		}, 10000);
    	}
    	document.addEventListener('DOMContentLoaded', initialize_notifications);
    	{% endif %}
  	</script>
	{% endblock %}
    </body>
</html>
