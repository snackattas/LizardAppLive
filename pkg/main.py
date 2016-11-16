from pkg import app, db, session
from databaseSetup import User, Lizard, Hobby
from databaseSetup import ChangeLog

from flask import render_template, request, redirect, url_for, flash
from flask import session as login_session

import httplib
import urlparse
import requests
from urllib2 import urlopen

from functools import wraps
import datetime
import os
import arrow

# Helper Functions
def requires_login(function):
    """requires_login: a decorator for routes that are designed to be accessible
    only when logged in"""
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if "username" not in login_session:
            # Flash error message if trying to access showHobby or other
            # restricted route
            if function.__name__ != "showLizard":
                flash("You need to be signed in to contribute to the database")
            return redirect(url_for("showPublicLizard"))
        return function(*args, **kwargs)
    return decorated_function


def requires_creator(function):
    """requires_creator: a decorator for routes that are designed to be
    accessible only when logged in as the same user as the creator of the
    lizard being edited/deleted"""
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if "username" not in login_session:
            flash("You need to be signed in to contribute to the database")
            return redirect(url_for("showPublicLizard"))
        lizard = Lizard.query.filter_by(id=kwargs["lizard_id"]).all()
        if not lizard:
            flash("This lizard does not exist or no longer exists")
            return redirect(url_for("showLizard"))
        if lizard[0].user_id != login_session["user_id"]:
            # Flash error message if trying to access addHobby, editHobby or
            # deleteHobby
            if function.__name__ != "showHobby":
                flash("Only the creator of this hobby can edit it")
            return redirect(url_for("showPublicHobby",
                                    lizard_id=kwargs["lizard_id"]))
        return function(*args, **kwargs)
    return decorated_function


def isURLImage(url):
    """isURLImage: Checks if the content-type of the url passed in is an image
    url via a HEAD request, for less overhead

    Args:
        url: url must meet certain qualifications
            - Must have a content-type of image/png, image/jpeg, image/jpg, or
              image/svg+xml
            - Must have content-length of less than 3MB
    Returns:
        url: If url meets qualifications, it will be returned; if url is
             incorrect, null will be returned
        error: If url meets qualifications, null will be returned; if url is
               incorrect, a specific error message will be returned
    Example:
        url = http://www.google.com/logos/doodles/2015/winter-solstice-2015-brazil-5991092264632320-hp2x.jpg"
        (url, error) = IsURLImage(url)
        if error:
            return render_template("error.html", error=error)
        """

    scheme, host, path, params, query, fragment = urlparse.urlparse(url)
    if not path:
        path = "/"
    if params:
        path = path + ";" + params
    if query:
        path = path + "?" + query
    try:
    # make a http HEAD request
        h = httplib.HTTP(host)
        h.putrequest("HEAD", path)
        h.putheader("Host", host)
        h.endheaders()

        status, reason, headers = h.getreply()
        # Convert byte size to megabytes
        image_type = headers.get("content-type")
        acceptable_image_types = ["image/png", "image/jpeg", "image/jpg",
            "image/svg+xml"]
        if image_type not in acceptable_image_types:
            error = "Only image URLs accepted: %s" % (url)
            h.close()
            return ("", error)
        size = headers.get("content-length")
        if not size:
            error = "Can't determine size of image from HTTP request: %s" % (url)
            h.close()
            return ("", error)
        size = float(size) / 1000000.0
        if size > 3.0:
            error = "Only supports images that are less than 3 MB: %s" % (url)
            h.close()
            return ("", error)
        h.close()
    except:
        error = "Invalid url: %s" % (url)
        return ("", error)
    
    # Now determine whether https or http is safe protocol
    https_url = ""
    http_url = ""
    if url.find("https://") > -1:
        https_url = url
        http_url = url.replace("https://", "http://")
    if url.find("http://") > -1:
        https_url = url.replace("http://", "https://")
        http_url = url
    if not https_url and not http_url:
        https_url = "https://" + url
        http_url = "http://" + url

    # Check https first:
    if certificate(http_url):
        return (url, "")
    if cerificate(https_url):
        return (url, "")
    return (url, "This site is blocked over HTTP and HTTPS")
    
    # result = certificate(https_url)
    # if certificate(https_url):
    #     return (url, "")
    # else:
    #     result, error = certificate(http_url)
    #     if result:
    #         return (url, "")
    # return (url, error)

def certificate(url):
	TIMEOUT=1
	result = False
	try:
		# Open URL
		url_open = urlopen(url, timeout=TIMEOUT)
		url_open.close()
		result = True
		return result
	except:
	    return result
	return result


def pretty_date(time):
    return arrow.get(time).humanize()

def recentActivity():
    """recentActivity: Returns the 10 latest changes (add, delete, update) to
                lizards and hobbies, in descending order"""
    return ChangeLog.query.order_by(db.desc("update_instant")).limit(10).all()


# Public routes, do not require login
@app.route("/")
@app.route("/publicLizard/")
def showPublicLizard():
    """showPublicLizard: Displays lizards, does not require login

    Routes:
        "/"
        "/publicLizard/"""""
    lizards = Lizard.query.order_by(db.asc(Lizard.name)).all()
    total_lizards = len(lizards)
    return render_template("publicLizard.html", lizards=lizards,
                           recent_activity=recentActivity(),
                           pretty_date=pretty_date,
                           total_lizards=total_lizards)


@app.route("/publicLizard/<int:lizard_id>/")
def showPublicHobby(lizard_id):
    """showPublicHobby: Displays hobbies from a particular lizard; does not
                       require login

    Arguments are derived from the url"""
    lizard = Lizard.query.filter_by(id=lizard_id).one()
    if not lizard:
        flash("This lizard does not exist")
        return redirect(url_for("showPublicLizard"))
    creator = User.query.filter_by(id=lizard.user_id).one()
    hobbies = Hobby.query.\
        filter_by(lizard_id=lizard.id).all()
    return render_template(
        "publicHobby.html", hobbies=hobbies, lizard=lizard,
        creator=creator, login_session=login_session)


# Routes to edit the database, all require login
@app.route("/lizard/")
@requires_login
def showLizard():
    "showLizard: Displays all lizards; requires login"
    lizards = Lizard.query.order_by(db.asc(Lizard.name)).all()
    total_lizards = len(lizards)
    return render_template("lizard.html", lizards=lizards,
                           login_session=login_session,
                           recent_activity=recentActivity(),
                           pretty_date=pretty_date,
                           total_lizards=total_lizards)


@app.route("/lizard/new/", methods=["GET", "POST"])
@requires_login
def newLizard():
    """newLizard: Displays new lizard creation form and posts new lizard
                    to the database; requires login"""
    if request.method == "GET":
        return render_template("newLizard.html", login_session=login_session)
    # First check to see if image URL is valid from HEAD reqauest.
    # If its not return error
    url = request.form.get("url")
    (url, error) = isURLImage(url)
    if error:
        return render_template("newLizard.html",
                               login_session=login_session,
                               error=error)
    # urlopen uses a GET request and does not accept HTTPS urls
    # try:
    #     url_open = urlopen(url)
    # except:
    #     error = "Unable to make a request to this URL: %s" % (url)
    #     return render_template("newLizard.html",
    #                           login_session=login_session,
    #                           error=error)
    # Create Lizard object
    new_lizard = Lizard(
        name=request.form.get("name"),
        user_id=login_session.get("user_id"),
        picture_url=url)

    session.add(new_lizard)
    session.commit()

    # After commit, retrieve lizard info to add to the ChangeLog
    newest_lizard = Lizard.query.\
        filter_by(user_id=login_session.get("user_id")).\
        order_by(db.desc("creation_instant")).limit(1)[0]

    change_log = ChangeLog(
        user_id=newest_lizard.user_id,
        lizard_name=newest_lizard.name,
        lizard_id=newest_lizard.id,
        update_instant=newest_lizard.creation_instant,
        action="new",
        table="lizard")
    session.add(change_log)
    flash("New Lizard %s Successfully Created" %\
        (newest_lizard.name))
    session.commit()
    return redirect(url_for("showLizard"))


@app.route("/lizard/<int:lizard_id>/edit/", methods=["GET", "POST"])
@requires_creator
def editLizard(lizard_id):
    """editLizard: Displays form to edit a lizard"s name and/or image url
                     and posts that information to the database; requires login

    Arguments are derived from the url"""
    edited_lizard = Lizard.query.filter_by(id=lizard_id).one()
    if request.method == "GET":
        return render_template("editLizard.html",
                               lizard=edited_lizard,
                               login_session=login_session)

    url = request.form.get("url")
    (url, error) = isURLImage(url)
    if error:
        return render_template("editLizard.html",
                               login_session=login_session,
                               lizard=edited_lizard,
                               error=error)
    # try:
    #     url_open = urlopen(url)
    # except:
    #     error = "Unable to make a request to this URL: %s" % (url)
    #     return render_template("editLizard.html",
    #                           login_session=login_session,
    #                           lizard=edited_lizard,
    #                           error=error)

    change_log = ChangeLog(
        user_id=edited_lizard.user_id,
        lizard_name=request.form.get("name"),
        lizard_id=lizard_id,
        update_instant=datetime.datetime.utcnow(),
        action="update",
        table="lizard")

    edited_lizard.name = request.form.get("name")
    edited_lizard.picture_url = url

    session.add(change_log)
    session.add(edited_lizard)
    flash("Lizard %s Successfully Edited"  % edited_lizard.name)
    session.commit()
    return redirect(url_for("showLizard"))


@app.route("/lizard/<int:lizard_id>/delete/", methods=["GET", "POST"])
@requires_creator
def deleteLizard(lizard_id):
    """deleteLizard: Displays form to delete a lizard and posts that
                       information to the database; requires login

    Arguments are derived from the url"""
    lizard_to_delete = Lizard.query.filter_by(id=lizard_id).one()
    if request.method == "GET":
        return render_template(
            "deleteLizard.html", lizard=lizard_to_delete,
            login_session=login_session)

    change_log = ChangeLog(
        user_id=lizard_to_delete.user_id,
        lizard_name=lizard_to_delete.name,
        update_instant=datetime.datetime.utcnow(),
        action="delete",
        table="lizard")

    session.add(change_log)

    # hobbies = Hobby.query.filter_by(lizard_id=lizard_to_delete.id)
    # for hobby in hobbies:
    #     HobbyImage.query.filter_by(hobby_id=hobby.id).delete()
    #     session.delete(hobby)
    session.delete(lizard_to_delete)
    flash("Lizard %s Successfully Deleted" % lizard_to_delete.name)
    session.commit()
    return redirect(url_for("showLizard"))



@app.route("/lizard/<int:lizard_id>/")
@requires_creator
def showHobby(lizard_id):
    """showHobby: Displays all hobbies of a particular lizard; requires login
                 and that the logged-in user is also the user that created the
                 lizard

    Args:
        lizard_id: : ID of the lizard being edited"""
    lizard = Lizard.query.filter_by(id=lizard_id).one()
    hobbies = Hobby.query.filter_by(lizard_id=lizard_id).all()
    creator = User.query.filter_by(id=lizard.user_id).one()
    return render_template(
        "hobby.html", hobbies=hobbies, lizard=lizard,
        login_session=login_session, creator=creator,
        user_id=login_session["user_id"])


@app.route("/lizard/<int:lizard_id>/new/", methods=["GET", "POST"])
@requires_creator
def newHobby(lizard_id):
    """newHobby: Displays new hobby creation form and posts new hobby to the
                database; requires login and that the logged-in user is also
                the user that created the lizard

    Arguments are derived from the url"""
    lizard = Lizard.query.filter_by(id=lizard_id).one()
    if request.method == "GET":
        return render_template("newHobby.html",
                               lizard=lizard,
                               login_session=login_session)

    url = request.form.get("url")
    (url, error) = isURLImage(url)
    if error:
        return render_template("newHobby.html",
                               login_session=login_session,
                               lizard=lizard,
                               error=error)
    # try:
    #     url_open = urlopen(url)
    # except:
    #     error = "Unable to make a request to this URL: %s" % (url)
    #     return render_template("newHobby.html",
    #                           login_session=login_session,
    #                           lizard=lizard,
    #                           error=error)

    new_hobby = Hobby(
        name=request.form.get("name"),
        description=request.form.get("description"),
        lizard_id=lizard_id,
        user_id=lizard.user_id,
        picture_url=url)

    session.add(new_hobby)
    flash("New Hobby %s Successfully Created" % (new_hobby.name))
    session.commit()

    newest_hobby = Hobby.query.\
        filter_by(user_id=lizard.user_id).\
        order_by(db.desc("creation_instant")).limit(1)[0]

    change_log = ChangeLog(
        user_id=lizard.user_id,
        lizard_name=lizard.name,
        lizard_id=lizard_id,
        hobby_name=newest_hobby.name,
        hobby_id=newest_hobby.id,
        update_instant=newest_hobby.creation_instant,
        action="new",
        table="hobby")

    session.add(change_log)
    session.commit()
    return redirect(url_for("showHobby", lizard_id=lizard_id))


@app.route(
    "/lizard/<int:lizard_id>/<int:hobby_id>/edit/",
    methods=["GET", "POST"])
@requires_creator
def editHobby(lizard_id, hobby_id):
    """editHobby: Displays form to edit a particular hobby's name, description,
                 and/or image url and posts that information to the database;
                 requires login and that the logged-in user is also the user
                 that created the lizard

    Arguments are derived from the url"""
    lizard = Lizard.query.filter_by(id=lizard_id).one()
    edited_hobby = Hobby.query.\
        filter_by(id=hobby_id, lizard_id=lizard_id).one()
    if request.method == "GET":
        return render_template("editHobby.html",
                               lizard=lizard,
                               hobby_id=hobby_id,
                               hobby=edited_hobby,
                               login_session=login_session)

    url = request.form.get("url")
    (url, error) = isURLImage(url)
    if error:
        return render_template("editHobby.html",
                               login_session=login_session,
                               lizard=lizard,
                               lizard_id=lizard_id,
                               hobby_id=hobby_id,
                               hobby=edited_hobby,
                               error=error)
    # try:
    #     url_open = urlopen(url)
    # except:
    #     error = "Unable to make a request to this URL: %s" % (url)
    #     return render_template("editHobby.html",
    #                           login_session=login_session,
    #                           lizard=lizard,
    #                           lizard_id=lizard_id,
    #                           hobby_id=hobby_id,
    #                           hobby=edited_hobby,
    #                           error=error)

    # The ChangeLog for editing hobbies will have an entry if any change is
    # made to an hobby
    # But the only metadata collected is the new hobby's name, even if the
    # name didn"t change
    change_log = ChangeLog(
        user_id=edited_hobby.user_id,
        lizard_name=lizard.name,
        lizard_id=lizard_id,
        hobby_name=request.form.get("name"),
        hobby_id=hobby_id,
        update_instant=datetime.datetime.utcnow(),
        action="update",
        table="hobby")

    edited_hobby.name = request.form.get("name")
    edited_hobby.description = request.form.get("description")
    edited_hobby.picture_url = url

    session.add(change_log)
    flash("Hobby %s Successfully Edited" % (edited_hobby.name))
    session.commit()
    return redirect(url_for("showHobby", lizard_id=lizard_id))


@app.route(
    "/lizard/<int:lizard_id>/<int:hobby_id>/delete/",
    methods=["GET", "POST"])
@requires_creator
def deleteHobby(lizard_id, hobby_id):
    """deleteHobby: Displays form to delete an hobby and posts that information
                   to the database; requires login and that the logged-in user
                   is also the user that created the lizard

    Arguments are derived from the url"""
    lizard = Lizard.query.filter_by(id=lizard_id).one()
    hobby_to_delete = Hobby.query.\
        filter_by(id=hobby_id, lizard_id=lizard_id).one()
    if request.method == "GET":
        return render_template("deleteHobby.html", lizard=lizard,
        hobby=hobby_to_delete, login_session=login_session)

    change_log = ChangeLog(
        user_id=hobby_to_delete.user_id,
        lizard_name=lizard.name,
        lizard_id=lizard_id,
        hobby_name=hobby_to_delete.name,
        update_instant=datetime.datetime.utcnow(),
        action="delete",
        table="hobby")

    session.add(change_log)
    session.delete(hobby_to_delete)
    flash("Hobby %s Successfully Deleted" % (hobby_to_delete.name))
    session.commit()
    return redirect(url_for("showHobby", lizard_id=lizard_id))


# @app.route("/error/")
# @app.errorhandler(304)
# @app.errorhandler(404)
# @app.errorhandler(500)
# def pageNotFound(error):
#     return render_template("pageNotFound.html", error=error), 404
