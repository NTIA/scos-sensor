# admin_password.rb
Facter.add('admin_password') do
   setcode '/bin/cat /opt/scos-sensor/.admin_password'
end
