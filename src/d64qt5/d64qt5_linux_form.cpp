// Stage 488: Native Linux Qt5 FORM entrypoint built into libd64_qt5.so.
// Uses the project's existing d64qt5_bridge C ABI, Qt5 build and WFM JSON
// representation. No embedded Python/PyQt5 interpreter is required.
#include "d64qt5_bridge.h"

#ifndef _WIN32
#include <QApplication>
#include <QThread>
#include <QGuiApplication>
#include <QDesktopServices>
#include <QProcess>
#include <QUrl>
#include <QFileInfo>
#include <QMessageBox>
#include <QVariant>
#include <cstdint>
#include <QCheckBox>
#include <QComboBox>
#include <QDebug>
#include <QGroupBox>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonParseError>
#include <QLabel>
#include <QLineEdit>
#include <QListWidget>
#include <QPlainTextEdit>
#include <QProgressBar>
#include <QDialog>
#include <QVBoxLayout>
#include <QTextCursor>
#include <QPushButton>
#include <QRadioButton>
#include <QTextEdit>
#include <QWidget>
#include <QHash>
#include <QByteArray>
#include <QVariant>
#include <QMetaObject>
#include <QAbstractButton>
#include <QString>
#include <QVector>
#include <cstdio>
#include <memory>

namespace {
QJsonValue property(const QJsonObject &object, const QString &name,
                    const QJsonValue &fallback = QJsonValue()) {
    for (auto it=object.constBegin(); it!=object.constEnd(); ++it)
        if (it.key().compare(name, Qt::CaseInsensitive)==0) return it.value();
    return fallback;
}
QString str(const QJsonValue &v, const QString &fallback=QString()) {
    if (v.isUndefined() || v.isNull()) return fallback;
    return v.isString() ? v.toString() : v.toVariant().toString();
}
int number(const QJsonObject &p, const QString &key, int fallback) {
    bool good=false;
    int value=str(property(p,key)).toDouble(&good);
    return good ? value : fallback;
}
QWidget *newWidget(const QString &name, QWidget *parent) {
    QString c=name.toLower();
    if (c=="button" || c=="pushbutton" || c=="commandbutton") return new QPushButton(parent);
    if (c=="label" || c=="statictext") return new QLabel(parent);
    if (c=="edit" || c=="lineedit" || c=="textbox") return new QLineEdit(parent);
    if (c=="memo" || c=="textedit") return new QTextEdit(parent);
    if (c=="checkbox") return new QCheckBox(parent);
    if (c=="radiobutton") return new QRadioButton(parent);
    if (c=="combobox") return new QComboBox(parent);
    if (c=="listbox") return new QListWidget(parent);
    if (c=="groupbox") return new QGroupBox(parent);
    if (c=="progressbar") return new QProgressBar(parent);
    return nullptr;
}
void setText(QWidget *w, const QString &text) {
    if (auto *edit=qobject_cast<QLineEdit*>(w)) edit->setText(text);
    else if (auto *label=qobject_cast<QLabel*>(w)) label->setText(text);
    else if (auto *button=qobject_cast<QAbstractButton*>(w)) button->setText(text);
    else if (auto *memo=qobject_cast<QTextEdit*>(w)) memo->setPlainText(text);
    else if (auto *group=qobject_cast<QGroupBox*>(w)) group->setTitle(text);
    else w->setWindowTitle(text);
}
// Unified native Qt5 terminal for Linux dBASE .prg and WFM output.
// Uses a separate, user-closeable QDialog with a read-only QPlainTextEdit.
class DBaseTerminalDialog final : public QDialog {
public:
    explicit DBaseTerminalDialog(QWidget *owner = nullptr) : QDialog(owner) {
        setObjectName(QStringLiteral("dbaseTerminalDialog"));
        setWindowTitle(QStringLiteral("dBASE Qt5 Terminal"));
        setWindowFlags(Qt::Window | Qt::WindowSystemMenuHint | Qt::WindowCloseButtonHint);
        resize(700, 360);
        auto *layout = new QVBoxLayout(this);
        editor = new QPlainTextEdit(this);
        editor->setObjectName(QStringLiteral("dbaseTerminalOutput"));
        editor->setReadOnly(true);
        editor->setUndoRedoEnabled(false);
        editor->setLineWrapMode(QPlainTextEdit::NoWrap);
        editor->setStyleSheet(QStringLiteral(
            "QPlainTextEdit { background: #000080; color: #ffff00; "
            "font-family: monospace; font-size: 11pt; border: 1px solid #7272b0; }"));
        layout->addWidget(editor);
    }
    void writeText(const QString &text) {
        if (text.isEmpty()) return;
        QTextCursor cursor = editor->textCursor();
        cursor.movePosition(QTextCursor::End);
        cursor.insertText(text);
        editor->setTextCursor(cursor);
        editor->ensureCursorVisible();
        if (!isVisible()) show();
    }
private:
    QPlainTextEdit *editor = nullptr;
};

void appendJsonOutput(DBaseTerminalDialog *terminal, const QJsonArray &output) {
    if (!terminal) return;
    for (const auto &chunk : output)
        terminal->writeText(chunk.toString());
}

// Qt operates with QWidget pointers, while X11 exposes numeric XIDs. Never
// return a made-up XID for Wayland. A native X11 WId exists with the xcb QPA.
quintptr nativeX11Id(QWidget *window) {
    if (!window || !QGuiApplication::platformName().startsWith(QLatin1String("xcb")))
        return 0;
    return static_cast<quintptr>(window->winId());
}

QVariant compatArgument(const QJsonValue &value, const QHash<QString,QVariant> &variables,
                        QWidget *form) {
    if (value.isObject()) {
        QJsonObject data=value.toObject();
        if (data.value(QStringLiteral("x11_window")).toBool())
            return QVariant::fromValue(static_cast<qulonglong>(nativeX11Id(form)));
        if (data.contains(QStringLiteral("variable")))
            return variables.value(data.value(QStringLiteral("variable")).toString().toLower());
    }
    return value.toVariant();
}

// Only a consciously implemented Shell32/User32 compatibility subset.
// 33 means success (as ShellExecute returns >32); 2 means not found.
qlonglong qtShellExecute(const QString &operation, const QString &file,
                         const QString &parameters, const QString &directory) {
    if (file.isEmpty()) return 2;
    if (!operation.isEmpty() && operation.compare(QStringLiteral("open"),Qt::CaseInsensitive)!=0)
        return 31; // SE_ERR_NOASSOC: unsupported verb for this compatibility shim
    const QUrl url=QUrl::fromUserInput(file);
    if ((url.scheme()==QStringLiteral("https") || url.scheme()==QStringLiteral("http") ||
         url.scheme()==QStringLiteral("mailto")) && parameters.isEmpty())
        return QDesktopServices::openUrl(url) ? 33 : 2;
    if (parameters.isEmpty() && QFileInfo::exists(file) && !QFileInfo(file).isExecutable())
        return QDesktopServices::openUrl(QUrl::fromLocalFile(QFileInfo(file).absoluteFilePath())) ? 33 : 2;
    const QStringList args=QProcess::splitCommand(parameters);
    return QProcess::startDetached(file,args,directory) ? 33 : 2;
}

// Win32 MessageBox flags translated into Qt5 buttons/icons. The return value
// deliberately keeps the Win32 ID* constants, so unchanged dBASE callers can
// branch on IDYES, IDCANCEL etc. No arbitrary HWND is cast to QWidget*.
QWidget *windowForX11Id(std::uintptr_t hwnd) {
    if (!hwnd || !QApplication::instance() ||
        !QGuiApplication::platformName().startsWith(QLatin1String("xcb")))
        return nullptr;
    // A WFM onClick Sender may identify the button (a native child XID),
    // not only the form. Resolve both to the owning top-level widget.
    for (QWidget *widget : QApplication::allWidgets()) {
        if (widget && widget->testAttribute(Qt::WA_WState_Created) &&
            nativeX11Id(widget)==static_cast<quintptr>(hwnd)) return widget->window();
    }
    return nullptr;
}

int showWin32MessageBox(std::uintptr_t hwnd, const QString &message,
                         const QString &caption, unsigned int flags) {
    QApplication *app=qobject_cast<QApplication*>(QCoreApplication::instance());
    if (QCoreApplication::instance() && (!app || QThread::currentThread()!=app->thread())) {
        qWarning("MessageBoxA: QMessageBox erfordert den Qt5-GUI-Hauptthread.");
        return 0;
    }
    // Also permit direct ctypes/dlsym calls before the WFM runtime starts.
    int argc=1;
    char program[]="dBASE-MessageBox";
    char *argv[]={program,nullptr};
    std::unique_ptr<QApplication> owned;
    if (!app) {
        owned.reset(new QApplication(argc,argv));
        app=owned.get();
    }
    QMessageBox::StandardButtons buttons;
    switch (flags & 0x0fU) {
    case 0x01U: buttons=QMessageBox::Ok | QMessageBox::Cancel; break;
    case 0x02U: buttons=QMessageBox::Abort | QMessageBox::Retry | QMessageBox::Ignore; break;
    case 0x03U: buttons=QMessageBox::Yes | QMessageBox::No | QMessageBox::Cancel; break;
    case 0x04U: buttons=QMessageBox::Yes | QMessageBox::No; break;
    case 0x05U: buttons=QMessageBox::Retry | QMessageBox::Cancel; break;
    case 0x06U: buttons=QMessageBox::Cancel; break;  // extra IDTRYAGAIN/IDCONTINUE buttons
    default:    buttons=QMessageBox::Ok; break;
    }
    QMessageBox::Icon icon=QMessageBox::NoIcon;
    switch (flags & 0xF0U) {
    case 0x10U: icon=QMessageBox::Critical; break;  // MB_ICONHAND
    case 0x20U: icon=QMessageBox::Question; break;  // MB_ICONQUESTION
    case 0x30U: icon=QMessageBox::Warning; break;   // MB_ICONEXCLAMATION
    case 0x40U: icon=QMessageBox::Information; break; // MB_ICONASTERISK
    }
    QMessageBox box(icon,caption,message,buttons,windowForX11Id(hwnd));
    QAbstractButton *tryAgain=nullptr;
    QAbstractButton *continueButton=nullptr;
    if ((flags & 0x0fU)==0x06U) {
        tryAgain=box.addButton(QStringLiteral("Erneut versuchen"), QMessageBox::AcceptRole);
        continueButton=box.addButton(QStringLiteral("Fortsetzen"), QMessageBox::ActionRole);
    }
    box.setWindowModality(Qt::ApplicationModal);
    QMessageBox::StandardButton order[]={
        QMessageBox::Ok, QMessageBox::Cancel, QMessageBox::Abort,
        QMessageBox::Retry, QMessageBox::Ignore, QMessageBox::Yes,
        QMessageBox::No
    };
    const unsigned choice=(flags & 0x300U)/0x100U;
    unsigned pos=0;
    for (auto button:order) {
        if (buttons.testFlag(button)) {
            if (pos==choice) { box.setDefaultButton(button); break; }
            ++pos;
        }
    }
    const int pressed=box.exec();
    if (tryAgain && box.clickedButton()==tryAgain) return 10; // IDTRYAGAIN
    if (continueButton && box.clickedButton()==continueButton) return 11; // IDCONTINUE
    switch (pressed) {
    case QMessageBox::Ok:     return 1;  // IDOK
    case QMessageBox::Cancel: return 2;  // IDCANCEL
    case QMessageBox::Abort:  return 3;  // IDABORT
    case QMessageBox::Retry:  return 4;  // IDRETRY
    case QMessageBox::Ignore: return 5;  // IDIGNORE
    case QMessageBox::Yes:    return 6;  // IDYES
    case QMessageBox::No:     return 7;  // IDNO
    default:                  return 0;  // error/dismissed
    }
}

QVariant qtCompatCall(const QString &entry, const QJsonArray &argv,
                      QHash<QString,QVariant> &variables, QWidget *form) {
    QVariantList args;
    for (const auto &value:argv) args << compatArgument(value,variables,form);
    const QString call=entry.toLower();
    if (call==QLatin1String("shellexecutea") || call==QLatin1String("shellexecutew")) {
        if (args.size()!=6) return 2;
        return qtShellExecute(args.at(1).toString(),args.at(2).toString(),
                              args.at(3).toString(),args.at(4).toString());
    }
    if (call==QLatin1String("messageboxa") || call==QLatin1String("messageboxw")) {
        if (args.size()!=4) return 0;
        // Call the SAME exported C ABI as native ELF callers. On X11 the
        // HWND argument is an XID, never a fabricated QWidget pointer.
        const std::uintptr_t hwnd=static_cast<std::uintptr_t>(args.at(0).toULongLong());
        const QByteArray text=args.at(1).toString().toLocal8Bit();
        const QByteArray caption=args.at(2).toString().toLocal8Bit();
        const unsigned flags=args.at(3).toUInt();
        if (call==QLatin1String("messageboxa"))
            return ::MessageBoxA(hwnd,text.constData(),caption.constData(),flags);
        const QString wtext=args.at(1).toString();
        const QString wcaption=args.at(2).toString();
        return showWin32MessageBox(hwnd,wtext,wcaption,flags);
    }
    qWarning().noquote() << "dBASE Linux: nicht implementierter FFI-Aufruf:" << entry;
    return 0;
}

QVariant runDBaseActions(const QJsonArray &actions, DBaseTerminalDialog *terminal,
                     QWidget *form, const QHash<QString,QWidget*> &widgets = {},
                     const QHash<QString,QVariant> &initialVariables = {}) {
    // Event arguments are bound when clicked(bool) fires. Unlike the old
    // action interpreter, the variables table is now initialized from the
    // event's declared Sender/Checked parameters.
    QHash<QString,QVariant> variables = initialVariables;
    for (const auto &entry:actions) {
        const QJsonArray args=entry.toArray();
        if (args.isEmpty()) continue;
        const QString command=args.at(0).toString();
        if (command==QLatin1String("print")) {
            terminal->writeText(args.at(1).toString()+
                                (args.at(2).toBool() ? QStringLiteral("\n") : QString()));
        } else if (command==QLatin1String("settext")) {
            QWidget *target=widgets.value(args.at(1).toString().toLower(),nullptr);
            if (target) setText(target,args.at(2).toString());
        } else if (command==QLatin1String("settext_value")) {
            QWidget *target=widgets.value(args.at(1).toString().toLower(),nullptr);
            if (target) setText(target,compatArgument(args.at(2),variables,form).toString());
        } else if (command==QLatin1String("set_var")) {
            variables.insert(args.at(1).toString().toLower(),
                             compatArgument(args.at(2),variables,form));
        } else if (command==QLatin1String("print_value")) {
            const QVariant result=compatArgument(args.at(1),variables,form);
            terminal->writeText(result.toString()+
                                (args.at(2).toBool() ? QStringLiteral("\n") : QString()));
        } else if (command==QLatin1String("return")) {
            return args.size()>1 ? compatArgument(args.at(1),variables,form) : QVariant();
        } else if (command==QLatin1String("ffi_return")) {
            return qtCompatCall(args.at(1).toString(),args.at(2).toArray(),variables,form);
        } else if (command==QLatin1String("ffi_call") || command==QLatin1String("ffi_print")) {
            const QVariant result=qtCompatCall(args.at(1).toString(),args.at(2).toArray(),variables,form);
            if (command==QLatin1String("ffi_call") && args.size()>3 && !args.at(3).toString().isEmpty())
                variables.insert(args.at(3).toString().toLower(),result);
            if (command==QLatin1String("ffi_print"))
                terminal->writeText(result.toString()+
                                    (args.at(3).toBool() ? QStringLiteral("\n") : QString()));
        } else if (command==QLatin1String("print_var")) {
            const QVariant value=variables.value(args.at(1).toString().toLower());
            terminal->writeText(value.toString()+
                                (args.at(2).toBool() ? QStringLiteral("\n") : QString()));
        }
    }
    return QVariant();
}

void applyProperties(QWidget *w, const QJsonObject &props, bool root=false) {
    QJsonValue text=property(props,"Caption",property(props,"Text"));
    if (!text.isUndefined()) setText(w,str(text));
    if (auto *edit=qobject_cast<QLineEdit*>(w)) {
        QJsonValue placeholder=property(props,"PlaceholderText",property(props,"Placeholder"));
        if (!placeholder.isUndefined()) edit->setPlaceholderText(str(placeholder));
    }
    QJsonValue enabled=property(props,"Enabled");
    if (!enabled.isUndefined()) w->setEnabled(enabled.toBool(true));
    QJsonValue visible=property(props,"Visible");
    if (!visible.isUndefined() && !visible.toBool(true)) w->hide();
    if (auto *b=qobject_cast<QAbstractButton*>(w)) {
        QJsonValue checked=property(props,"Checked");
        if (!checked.isUndefined()) b->setChecked(checked.toBool());
    }
    if (root) w->resize(qMax(1,number(props,"Width",640)), qMax(1,number(props,"Height",480)));
    else w->setGeometry(number(props,"Left",0),number(props,"Top",0),
                        qMax(1,number(props,"Width",100)),qMax(1,number(props,"Height",25)));
}
}

extern "C" D64QT5_API std::intptr_t ShellExecuteA(std::uintptr_t /*hwnd*/, const char *verb,
                    const char *filename, const char *parameters,
                    const char *directory, int /*showCommand*/) {
    return static_cast<std::intptr_t>(qtShellExecute(QString::fromLocal8Bit(verb ? verb : ""),
        QString::fromLocal8Bit(filename ? filename : ""),
        QString::fromLocal8Bit(parameters ? parameters : ""),
        QString::fromLocal8Bit(directory ? directory : "")));
}
extern "C" D64QT5_API std::intptr_t ShellExecuteW(std::uintptr_t /*hwnd*/, const char16_t *verb,
                    const char16_t *filename, const char16_t *parameters,
                    const char16_t *directory, int /*showCommand*/) {
    auto toString=[](const char16_t *data) {
        if (!data) return QString();
        const char16_t *end=data;
        while (*end) ++end;
        return QString::fromUtf16(reinterpret_cast<const ushort*>(data),int(end-data));
    };
    return static_cast<std::intptr_t>(qtShellExecute(toString(verb),toString(filename),
                                                       toString(parameters),toString(directory)));
}
// Native exports for Linux FFI callers: e.g. extern CINT MessageBoxA(...)
// "user32.so" from "MessageBoxA". The .so alias is built as a symlink to
// libd64_qt5.so; unlike Windows, this is a *limited* Qt implementation.
extern "C" D64QT5_API int MessageBoxA(std::uintptr_t hwnd, const char *message,
                                       const char *caption, unsigned int type) {
    return showWin32MessageBox(hwnd,QString::fromLocal8Bit(message ? message : ""),
                                QString::fromLocal8Bit(caption ? caption : ""),type);
}
extern "C" D64QT5_API int MessageBoxW(std::uintptr_t hwnd, const uint16_t *message,
                                       const uint16_t *caption, unsigned int type) {
    auto decode=[](const uint16_t *text) -> QString {
        if (!text) return QString();
        const uint16_t *end=text;
        while (*end) ++end;
        return QString::fromUtf16(reinterpret_cast<const ushort*>(text),int(end-text));
    };
    return showWin32MessageBox(hwnd,decode(message),decode(caption),type);
}

extern "C" D64QT5_API std::uintptr_t DBaseQtGetX11WindowId(void *widget) {
    return static_cast<std::uintptr_t>(nativeX11Id(static_cast<QWidget*>(widget)));
}

extern "C" D64QT5_API int DBaseQtRunConsoleJson(const char *utf8Json) {
    if (!utf8Json) return 65;
    QJsonParseError error;
    QJsonDocument document=QJsonDocument::fromJson(QByteArray(utf8Json),&error);
    if (error.error != QJsonParseError::NoError || !document.isObject()) return 65;
    int argc=1;
    char argv0[]="dBASE-Terminal";
    char *argv[]={argv0,nullptr};
    std::unique_ptr<QApplication> owned;
    if (!QApplication::instance()) owned.reset(new QApplication(argc,argv));
    DBaseTerminalDialog terminal;
    QString title=str(property(document.object(),"title"));
    if (!title.isEmpty()) terminal.setWindowTitle(title);
    const QJsonArray actions=property(document.object(),"actions").toArray();
    if (!actions.isEmpty()) runDBaseActions(actions,&terminal,nullptr);
    else appendJsonOutput(&terminal,property(document.object(),"output").toArray());
    if (!terminal.isVisible()) terminal.show();
    if (!owned) return 0;
    return owned->exec();
}

extern "C" D64QT5_API int DBaseQtRunFormJson(const char *utf8Json) {
    if (!utf8Json) return 65;
    QJsonParseError error;
    auto document=QJsonDocument::fromJson(QByteArray(utf8Json),&error);
    if (error.error!=QJsonParseError::NoError || !document.isObject()) {
        qCritical().noquote() << "dBASE WFM Linux: ungueltiges FORM-JSON:" << error.errorString();
        return 65;
    }
    int argc=1;
    char argv0[]="dBASE-WFM";
    char *argv[]={argv0,nullptr};
    std::unique_ptr<QApplication> ownApplication;
    if (!QApplication::instance()) ownApplication.reset(new QApplication(argc,argv));
    QJsonObject formJson=document.object();
    std::unique_ptr<QWidget> form(new QWidget());
    QString formName=str(property(formJson,"name"),"Form1");
    QJsonObject formProps=property(formJson,"properties").toObject();
    form->setWindowTitle(str(property(formProps,"Caption"),formName));
    applyProperties(form.get(),formProps,true);
    QHash<QString,QWidget*> widgets;
    widgets.insert("this",form.get());
    widgets.insert(formName.toLower(),form.get());
    QJsonArray controls=property(formJson,"controls").toArray();
    for (const auto &item: controls) {
        auto control=item.toObject();
        QString path=str(property(control,"path")).toLower();
        QString parentPath=str(property(control,"parent")).toLower();
        QWidget *parent=widgets.value(parentPath,form.get());
        QWidget *widget=newWidget(str(property(control,"class")),parent);
        if (!widget) {
            qCritical().noquote() << "dBASE WFM Linux: Steuerelement nicht implementiert:" << str(property(control,"class"));
            return 78;
        }
        widgets.insert(path,widget);
        applyProperties(widget,property(control,"properties").toObject());
    }
    DBaseTerminalDialog terminal(form.get());
    const QJsonArray startup=property(formJson,"startup_actions").toArray();
    if (!startup.isEmpty()) runDBaseActions(startup,&terminal,form.get(),widgets);
    else appendJsonOutput(&terminal, property(formJson,"startup_output").toArray());
    QJsonObject methods=property(formJson,"methods").toObject();
    for (const auto &item: controls) {
        auto control=item.toObject();
        QString path=str(property(control,"path")).toLower();
        QWidget *widget=widgets.value(path);
        QJsonObject events=property(control,"events").toObject();
        QString handler=str(property(events,"onClick"));
        if (handler.isEmpty()) continue;
        QString method=handler.split("::").last().trimmed().toLower();
        QJsonArray actions;
        QJsonArray parameters;
        bool found=false;
        for (auto it=methods.constBegin(); it!=methods.constEnd(); ++it) {
            if (it.key().compare(method,Qt::CaseInsensitive)!=0) continue;
            found=true;
            // Stage 492: parameterless procedures retain the old JSON array
            // schema. Parameterized procedures/functions contain metadata.
            if (it.value().isObject()) {
                const QJsonObject specification=it.value().toObject();
                actions=specification.value(QStringLiteral("actions")).toArray();
                parameters=specification.value(QStringLiteral("parameters")).toArray();
            } else {
                actions=it.value().toArray();
            }
            break;
        }
        if (!found) {
            qCritical().noquote() << "dBASE WFM Linux: Ereignismethode fehlt:" << method;
            return 78;
        }
        auto *button=qobject_cast<QAbstractButton*>(widget);
        if (!button) {
            qCritical().noquote() << "dBASE WFM Linux: onClick fuer Steuerelement nicht implementiert:" << path;
            return 78;
        }
        // Form and control pointers stay valid until QApplication::exec exits.
        QObject::connect(button, &QAbstractButton::clicked, form.get(),
                         [actions,parameters,widgets,button,&terminal](bool checked) {
            QHash<QString,QVariant> eventVariables;
            if (!parameters.isEmpty()) {
                const QString name=parameters.at(0).toString().toLower();
                // Qt onClick sends the control as Sender. On xcb this is its
                // native XID; Wayland never receives a fabricated X11 handle.
                const QVariant sender=QVariant::fromValue(
                    static_cast<qulonglong>(nativeX11Id(button)));
                eventVariables.insert(name, name==QLatin1String("checked")
                                      ? QVariant(checked) : sender);
            }
            if (parameters.size()>1)
                eventVariables.insert(parameters.at(1).toString().toLower(),checked);
            // Qt clicked(bool) ignores return values from FUNCTION handlers.
            (void)runDBaseActions(actions,&terminal,widgets.value("this"),widgets,eventVariables);
        });
    }
    form->show();
    // Existing QApplication instance can be an embedding host; do not own it.
    if (!ownApplication) return 0;
    return ownApplication->exec();
}
#else
extern "C" D64QT5_API int DBaseQtRunFormJson(const char *) { return 78; }
extern "C" D64QT5_API int DBaseQtRunConsoleJson(const char *) { return 78; }
#endif
