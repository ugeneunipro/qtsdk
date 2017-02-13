#!/usr/bin/env python
#############################################################################
##
## Copyright (C) 2013 Digia Plc and/or its subsidiary(-ies).
## Contact: http://www.qt-project.org/legal
##
## This file is part of the release tools of the Qt Toolkit.
##
## $QT_BEGIN_LICENSE:LGPL$
## Commercial License Usage
## Licensees holding valid commercial Qt licenses may use this file in
## accordance with the commercial license agreement provided with the
## Software or, alternatively, in accordance with the terms contained in
## a written agreement between you and Digia.  For licensing terms and
## conditions see http://qt.digia.com/licensing.  For further information
## use the contact form at http://qt.digia.com/contact-us.
##
## GNU Lesser General Public License Usage
## Alternatively, this file may be used under the terms of the GNU Lesser
## General Public License version 2.1 as published by the Free Software
## Foundation and appearing in the file LICENSE.LGPL included in the
## packaging of this file.  Please review the following information to
## ensure the GNU Lesser General Public License version 2.1 requirements
## will be met: http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
##
## In addition, as a special exception, Digia gives you certain additional
## rights.  These rights are described in the Digia Qt LGPL Exception
## version 1.1, included in the file LGPL_EXCEPTION.txt in this package.
##
## GNU General Public License Usage
## Alternatively, this file may be used under the terms of the GNU
## General Public License version 3.0 as published by the Free Software
## Foundation and appearing in the file LICENSE.GPL included in the
## packaging of this file.  Please review the following information to
## ensure the GNU General Public License version 3.0 requirements will be
## met: http://www.gnu.org/copyleft/gpl.html.
##
##
## $QT_END_LICENSE$
##
#############################################################################

# import the print function which is used in python 3.x
from __future__ import print_function

# built in imports
import argparse # commandline argument parser
import multiprocessing
import os
import subprocess
import sys

# own imports
from threadedwork import ThreadedWork
from bld_utils import gitSHA, runBuildCommand, runCommand, runInstallCommand, stripVars
import bldinstallercommon

def add_common_commandline_arguments(parser):
    if bldinstallercommon.is_win_platform():
        parser.epilog = "example: " + os.linesep + "\tpython {0} --clean " \
            "--buildcommand C:\\bin\\ibjom.cmd --installcommand nmake " \
            "--qt-module http://it-dl241-hki.it.local/packages/qt/5.5.0-released/windows_vs2013_32/qt_all.7z " \
            "--sevenzippath \"C:\\Program Files\\7-Zip\" " \
            "--gitpath \"C:\\Program Files (x86)\\Git\\cmd\" "\
            "--d3dcompiler7z http://download.qt.io/development_releases/prebuilt/d3dcompiler/msvc2010/D3DCompiler_43-x86.dll.7z " \
            "--opengl32sw7z http://download.qt.io/development_releases/prebuilt/llvmpipe/windows/opengl32sw-32.7z " \
            "--environment_batch \"C:\\Program Files (x86)\\Microsoft Visual Studio 10.0\\VC\\vcvarsall.bat\" " \
            "--environment_batch_argument x86" \
            "".format(os.path.basename(sys.argv[0]))
    elif bldinstallercommon.is_mac_platform():
        parser.epilog = "example: " + os.linesep + "\tpython {0} --clean " \
            "--qt-module http://it-dl241-hki.it.local/packages/qt/5.0.1-released/mac_cocoa_10.7/qt_all.7z" \
            "".format(os.path.basename(sys.argv[0]))
    else:
        parser.epilog = "example: " + os.linesep + "\tpython {0} --clean " \
            "--qt-module http://it-dl241-hki.it.local/packages/qt/5.0.1-released/linux_gcc_64_ubuntu1110/qt_all.7z " \
            "--icu7z http://it-dl241-hki.it.local/packages/qt/5.0.1-released/linux_gcc_64_ubuntu1110/libicu_x86_64_ubuntu1110.7z" \
            "".format(os.path.basename(sys.argv[0]))

    # general arguments
    parser.add_argument('--clean', help="clean up everything from old builds", action='store_true', default=False)
    parser.add_argument('--buildcommand', help="this means usually make", default="make")
    parser.add_argument('--installcommand', help="this means usually make", default="make")
    parser.add_argument('--debug', help="use debug builds", action='store_true', default=False)
    parser.add_argument('--qt-module', help="Qt module package url (.7z) needed for building",
        action='append', dest='qt_modules')

    if bldinstallercommon.is_linux_platform():
        parser.add_argument('--icu7z', help="a file or url where it get icu libs as 7z", required=True)

    # if we are on windows, maybe we want some other arguments
    if bldinstallercommon.is_win_platform():
        parser.add_argument('--d3dcompiler7z', help="a file or url where it get d3dcompiler lib")
        parser.add_argument('--opengl32sw7z', help="a file or url where it get d3dcompiler lib")
        parser.add_argument('--openssl7z', help="a file or url where to get the openssl libs as 7z")
        parser.add_argument('--environment_batch', help="batch file that sets up environment")
        parser.add_argument('--environment_batch_argument', help="if the batch file needs an argument just add it with this argument")
        parser.add_argument('--sevenzippath', help="path where the 7zip binary is located")
        parser.add_argument('--gitpath', help="path where the git binary is located")

def qmake_binary(qt5_path):
    return os.path.abspath(os.path.join(qt5_path, 'bin', 'qmake'))

def patch_qt_pri_files(qt5_path):
    # fix paths in module .pri files
    qt_install_prefix = subprocess.check_output([os.path.join(qt5_path, 'bin', 'qmake'),
                                                 '-query', 'QT_INSTALL_PREFIX']).strip()
    print('install prefix: "{0}", qt5_path "{1}"'.format(qt_install_prefix, qt5_path))
    for (path, dirnames, filenames) in os.walk(os.path.join(qt5_path, 'mkspecs')):
        for filename in filenames:
            if not filename.endswith('.pri'):
                continue
            filepath = os.path.join(path, filename)
            print('patching "{0}"'.format(filepath))
            with open(filepath, 'r') as f:
                contents = f.read()
            contents = contents.replace(qt_install_prefix, qt5_path)
            with open(filepath, 'w') as f:
                f.write(contents)

def get_common_environment(qt5_path, caller_arguments):
    # PATH
    path_list = []
    # -- Qt
    path_list.append(os.path.abspath(os.path.join(qt5_path, 'bin')))
    # -- python
    path_list.append(os.path.dirname(sys.executable))
    if hasattr(caller_arguments, 'sevenzippath') and caller_arguments.sevenzippath:
        path_list.append(caller_arguments.sevenzippath)
    if hasattr(caller_arguments, 'gitpath') and caller_arguments.gitpath:
        path_list.append(caller_arguments.gitpath)

    environment = {"PATH": os.pathsep.join(path_list)}
    if bldinstallercommon.is_linux_platform():
        environment["LD_LIBRARY_PATH"] = os.path.join(qt5_path, 'lib')
        environment["QMAKESPEC"] = "linux-g++"
    if bldinstallercommon.is_mac_platform():
        environment["DYLD_FRAMEWORK_PATH"] = os.path.join(qt5_path, 'lib')
    if not bldinstallercommon.is_win_platform():
        environment["MAKEFLAGS"] = "-j" + str(multiprocessing.cpu_count() + 1)
    return environment


if __name__ == "__main__":
    bldinstallercommon.init_common_module(os.path.dirname(os.path.realpath(__file__)))

    # install an argument parser
    parser = argparse.ArgumentParser(description="build Qt 5 based Qt Creator",
        formatter_class=argparse.RawTextHelpFormatter)
    add_common_commandline_arguments(parser)
    parser.add_argument('--qt5path', help="here it expects a compiled Qt5", required=True)
    parser.add_argument('--versiondescription', help="version description to be shown in the about dialog, e.g. 'pre-2.7.2")
    if bldinstallercommon.is_mac_platform():
        parser.add_argument('--keychain_unlock_script', help="script for unlocking the keychain used for signing")
        parser.epilog += " --keychain_unlock_script $HOME/unlock-keychain.sh"

    parser.epilog += " --qt5path qtcreator_qt5"
    callerArguments = parser.parse_args()

    # cleanup some values inside the callerArguments object
    stripVars(callerArguments, "\"")
    if callerArguments.qt5path != os.path.abspath(callerArguments.qt5path):
        print("changing the value of --qt5path from {0} to {1}".format(callerArguments.qt5path,
            os.path.abspath(callerArguments.qt5path)))
        callerArguments.qt5path = os.path.abspath(callerArguments.qt5path)

    qtCreatorSourceDirectory = os.path.abspath('qt-creator')
    qtCreatorBuildDirectory = os.path.abspath(os.path.join(qtCreatorSourceDirectory,
        '..', 'qt-creator_build'))
    qtCreatorInstallDirectory = os.path.abspath(os.path.join(qtCreatorSourceDirectory,
        '..', 'qt-creator_install'))
    qtCreatorTempDevDirectory = os.path.abspath(os.path.join(qtCreatorSourceDirectory,
        '..', 'qt-creator_dev'))
    if bldinstallercommon.is_win_platform():
        cdbextSourceDirectory = os.path.join(qtCreatorSourceDirectory, 'src', 'libs', 'qtcreatorcdbext')
        cdbextBuildDirectory = os.path.abspath(os.path.join(qtCreatorSourceDirectory,
            '..', 'cdbextension_build'))
        cdbextInstallDirectory = os.path.abspath(os.path.join(qtCreatorSourceDirectory,
            '..', 'cdbextension_install'))

    tempPath = os.path.abspath(os.path.join(qtCreatorSourceDirectory,
        '..', 'qt-creator_temp'))

    # check mac setup
    if bldinstallercommon.is_mac_platform():
        if callerArguments.keychain_unlock_script:
            if not os.environ['SIGNING_IDENTITY']:
                print('error: Environment variable SIGNING_IDENTITY not set')
                sys.exit(1)

    # clean step
    if callerArguments.clean:
        print("##### {0} #####".format("clean old builds"))
        bldinstallercommon.remove_tree(callerArguments.qt5path)
        bldinstallercommon.remove_tree(qtCreatorBuildDirectory)
        bldinstallercommon.remove_tree(qtCreatorInstallDirectory)
        if bldinstallercommon.is_win_platform():
            bldinstallercommon.remove_tree(cdbextBuildDirectory)
            bldinstallercommon.remove_tree(cdbextInstallDirectory)
        bldinstallercommon.remove_tree(tempPath)

    if not os.path.lexists(callerArguments.qt5path) and not callerArguments.qt_modules:
        parser.print_help()
        print(("error: You have to pass the --qt-module argument if the {0} does not exist"
            + os.linesep + os.linesep).format(callerArguments.qt5path))
        sys.exit(1)

    qmakeBinary = qmake_binary(callerArguments.qt5path)

    download_packages_work = ThreadedWork("get and extract Qt 5 binaries")
    need_to_install_qt = not os.path.lexists(callerArguments.qt5path)
    if need_to_install_qt:
        download_packages_work.addTaskObject(bldinstallercommon.create_qt_download_task(
            callerArguments.qt_modules, callerArguments.qt5path, tempPath, callerArguments))

    # run get Qt 5 tasks
    if download_packages_work.taskNumber != 0:
        download_packages_work.run()

    if need_to_install_qt:
        patch_qt_pri_files(callerArguments.qt5path)
        bldinstallercommon.patch_qt(callerArguments.qt5path)

    ### lets start building

    environment = get_common_environment(callerArguments.qt5path, callerArguments)
    environment["INSTALL_BASENAME"] = "qt-creator"
    environment["INSTALLER_ARCHIVE"] = "qtcreator.7z"
    if callerArguments.debug:
        buildType = 'debug'
    else:
        buildType = 'release'
    buildGitSHA = gitSHA(qtCreatorSourceDirectory, callerArguments)
    qtCreatorProFile = os.path.join(qtCreatorSourceDirectory, 'qtcreator.pro')

    qmakeCommandArguments = "{0} QTC_PREFIX={1} DEFINES+=IDE_REVISION={2} CONFIG+={3}".format(
        qtCreatorProFile, qtCreatorInstallDirectory, buildGitSHA, buildType)

    # hack to ensure plugins depending on declarative are also compiled with 2.7.0/5.0.1
    qmakeCommandArguments += " QT_CONFIG+=declarative"

    if bldinstallercommon.is_mac_platform():
        qmakeCommandArguments += " QMAKE_MAC_SDK=macosx" # work around QTBUG-41238

    if sys.platform == "win32":  # allow app to run on Windows XP
        qmakeCommandArguments += " QMAKE_LFLAGS_WINDOWS=/SUBSYSTEM:WINDOWS,5.01"

    if callerArguments.versiondescription:
        qmakeCommandArguments += " DEFINES+=IDE_VERSION_DESCRIPTION={0}".format(callerArguments.versiondescription)

    runCommand("{0} {1}".format(qmakeBinary, qmakeCommandArguments), qtCreatorBuildDirectory,
        callerArguments = callerArguments, init_environment = environment)

    runBuildCommand(currentWorkingDirectory = qtCreatorBuildDirectory, callerArguments = callerArguments,
        init_environment = environment)

    # on windows the install command is usual nmake so single threaded
    # because docs is creating same directory at the same time sometimes
    runInstallCommand("docs", currentWorkingDirectory = qtCreatorBuildDirectory, callerArguments = callerArguments,
        init_environment = environment)

    if not bldinstallercommon.is_mac_platform():
        runInstallCommand('install install_docs', currentWorkingDirectory = qtCreatorBuildDirectory,
            callerArguments = callerArguments, init_environment = environment)

    runInstallCommand('deployqt', currentWorkingDirectory = qtCreatorBuildDirectory, callerArguments = callerArguments,
        init_environment = environment)

    if bldinstallercommon.is_mac_platform():
        if callerArguments.keychain_unlock_script:
            runCommand(callerArguments.keychain_unlock_script, qtCreatorBuildDirectory, callerArguments = callerArguments,
                init_environment = environment)
        # environment has to have SIGNING_IDENTITY, can have SIGNING_FLAGS
        runInstallCommand('codesign', currentWorkingDirectory = qtCreatorBuildDirectory,
            callerArguments = callerArguments, init_environment = environment)

    if bldinstallercommon.is_win_platform():
        runInstallCommand('deployartifacts', qtCreatorBuildDirectory,
            callerArguments = callerArguments, init_environment = environment)

    runInstallCommand('bindist_installer', qtCreatorBuildDirectory, callerArguments = callerArguments,
        init_environment = environment)

    if bldinstallercommon.is_mac_platform():
        runInstallCommand('dmg', qtCreatorBuildDirectory,
            callerArguments = callerArguments, init_environment = environment)

    # cdbextension
    if bldinstallercommon.is_win_platform():
        runCommand([qmakeBinary, 'QTC_PREFIX=' + cdbextInstallDirectory, 'CONFIG+=' + buildType, cdbextSourceDirectory],
                   cdbextBuildDirectory, callerArguments = callerArguments, init_environment = environment)
        runBuildCommand(currentWorkingDirectory = cdbextBuildDirectory,
                        callerArguments = callerArguments, init_environment = environment)
        runInstallCommand('install', currentWorkingDirectory = cdbextBuildDirectory,
                          callerArguments = callerArguments, init_environment = environment)
        runCommand(['7z.exe', 'a', '-mx9', os.path.join(qtCreatorBuildDirectory, 'qtcreatorcdbext.7z'),
                    os.path.join(cdbextInstallDirectory, '*')],
                    currentWorkingDirectory = qtCreatorBuildDirectory, callerArguments = callerArguments,
                    init_environment = environment)

    # dev package
    bldinstallercommon.remove_tree(qtCreatorTempDevDirectory)
    runCommand(['python', '-u', os.path.join(qtCreatorSourceDirectory, 'scripts', 'createDevPackage.py'),
                '--source', qtCreatorSourceDirectory, '--build', qtCreatorBuildDirectory,
                '--verbose', '-o', os.path.join(qtCreatorBuildDirectory, 'qtcreator_dev.7z'),
                qtCreatorTempDevDirectory],
                qtCreatorBuildDirectory, callerArguments = callerArguments, init_environment = environment)
