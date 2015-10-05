from flask import render_template, redirect, request, url_for, flash, session
from . import auth
from .forms import LoginForm
from .. import svr


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if svr.get_user(form.email.data, form.password.data):
            session['email'] = form.email.data
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid email or password')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
def logout():
    session.pop('email', None)
    flash('You have been logged out')
    return redirect(url_for('main.index'))