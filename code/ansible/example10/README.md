---
layout: default
permalink: /code/ansible/example10
---

# Templates

We'll use the `haproxy` as loadbalancer.
Of course, install is just like we did for apache.
But now configuration is a bit more tricky since we need to list all web servers in haproxy's configuration.
How can we do that?

## HAProxy configuration template

Ansible uses [Jinja2](http://jinja.pocoo.org/docs/), a templating engine for Python.
When you write Jinja2 templates, you can use any variable defined by Ansible.

For instance, if you want to output the inventory_name of the host the template is currently built for, you just can write `{{ inventory_hostname }}` in the Jinja template.

Or if you need the IP of the first ethernet interface (which ansible knows thanks to the `setup` module), you just write: {% raw %}`{{ ["ansible_default_ipv4"]["address"] }}`{% endraw %} in your template.

Jinja2 templates also support conditionals, for-loops, etc...

Let's make a `templates/` directory and create a Jinja template inside.
We'll call  it `haproxy.cfg.j2`.
We use the `.j2` extension by convention, to make it obvious that this  is a Jinja2 template, but this is not necessary.

{% raw %}
```jinja
global
    daemon
    maxconn 256

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

listen cluster
    bind {{ ansible_default_ipv4.address }}:80
    mode http
    stats enable
    balance roundrobin
    {% for backend in groups["web"] %}
    server {{ hostvars[backend]["ansible_default_ipv4"]["address"] }} {{ hostvars[backend]["ansible_default_ipv4"]["address"] }} check port 80
    {% endfor %}
    option httpchk HEAD /index.php HTTP/1.0
```
{% endraw %}

We have many new things going on here.

First, {% raw %}`{{ ["ansible_default_ipv4"]["address"] }}`{% endraw %} will be replaced by the IP of the load balancer on eth1.

Then, we have a loop.
This loop is used to build the backend servers list.
It will loop over every host listed in the `[web]` group (and put this host in the `backend` variable).
For each of the hosts it will render a line using host's facts.
All hosts' facts are exposed in the `hostvars` variable, so it's easy to access another host variables (like its hostname or in this case IP).

We could have written the host list by hand, since we have only 2 of them.
But we're hoping that the server will be very successful, and that we'll need a hundred of them.
Thus, adding servers to the configuration or swapping some out boils down to adding or removing hosts from the `[web]` group.

## HAProxy playbook

We've done the most difficult part of the job.
Writing a playbook to install and configure HAproxy is a breeze:

```yaml
- hosts: haproxy
  tasks:
    - name: Installs haproxy load balancer
      apt:
        pkg: haproxy
        state: present
        update_cache: yes

    - name: Pushes configuration
      template:
        src: templates/haproxy.cfg.j2
        dest: /etc/haproxy/haproxy.cfg
        mode: 0640
        owner: root
        group: root
      notify:
        - restart haproxy

    - name: Sets default starting flag to 1
      lineinfile:
        dest: /etc/default/haproxy
        regexp: "^ENABLED"
        line: "ENABLED=1"
      notify:
        - restart haproxy

  handlers:
    - name: restart haproxy
      service:
        name: haproxy
        state: restarted
```

Looks familiar, isn't it?
The only new module here is `template`, which has the same arguments as `copy`.
We also restrict this playbook to the group `haproxy`.

And now... let's try this out.
Since our inventory contains only hosts necessary for the cluster, we don't need to limit the host list and can even run both playbooks.
Well, to tell the truth, we must run both of them at the same time, since the haproxy playbook requires facts _from_ the two webservers.

```
$ ansible-playbook -i hosts apache.yml haproxy.yml

PLAY [web] *********************

GATHERING FACTS *********************
ok: [host1.example.org]
ok: [host2.example.org]

TASK: [Updates apt cache] *********************
ok: [host1.example.org]
ok: [host2.example.org]

TASK: [Installs necessary packages] *********************
ok: [host1.example.org] => (item=apache2,libapache2-mod-php5,git)
ok: [host2.example.org] => (item=apache2,libapache2-mod-php5,git)

TASK: [Push future default virtual host configuration] *********************
ok: [host2.example.org]
ok: [host1.example.org]

TASK: [Activates our virtualhost] *********************
changed: [host1.example.org]
changed: [host2.example.org]

TASK: [Check that our config is valid] *********************
changed: [host1.example.org]
changed: [host2.example.org]

TASK: [Rolling back - Restoring old default virtualhost] *********************
skipping: [host1.example.org]
skipping: [host2.example.org]

TASK: [Rolling back - Removing out virtualhost] *********************
skipping: [host1.example.org]
skipping: [host2.example.org]

TASK: [Rolling back - Ending playbook] *********************
skipping: [host1.example.org]
skipping: [host2.example.org]

TASK: [Deploy our awesome application] *********************
ok: [host2.example.org]
ok: [host1.example.org]

TASK: [Deactivates the default virtualhost] *********************
changed: [host1.example.org]
changed: [host2.example.org]

TASK: [Deactivates the default ssl virtualhost] *********************
changed: [host2.example.org]
changed: [host1.example.org]

NOTIFIED: [restart apache] *********************
changed: [host2.example.org]
changed: [host1.example.org]

PLAY RECAP *********************
host1.example.org              : ok=10   changed=5    unreachable=0    failed=0    
host2.example.org              : ok=10   changed=5    unreachable=0    failed=0    



PLAY [haproxy] *********************

GATHERING FACTS *********************
ok: [host0.example.org]

TASK: [Installs haproxy load balancer] *********************
changed: [host0.example.org]

TASK: [Pushes configuration] *********************
changed: [host0.example.org]

TASK: [Sets default starting flag to 1] *********************
changed: [host0.example.org]

NOTIFIED: [restart haproxy] *********************
changed: [host0.example.org]

PLAY RECAP *********************
host0.example.org              : ok=5    changed=4    unreachable=0    failed=0    
```

Looks good.
Now head to http://Z.Z.Z.Z/ and see the result.
Your cluster is deployed!

You can even peek at HAProxy's statistics at http://Z.Z.Z.Z/haproxy?stats.

Now on to the next chapter about "Variables again", in [example11](../example11).
