#pragma once
// Stage 631: Turbo-Vision-Werkzeugfenster im bestehenden Qt5-DOS-Viewport.
// Drei Programme (Taschenrechner, CP437-Zeichentabelle, 15-Puzzle),
// eine gemeinsame Rahmen-, Titelleisten-, Raster- und Fenstersteuerung.
// Kein Q_OBJECT / MOC.
#include "d64_turbo_calculator_expression.hpp"
#include "d64_turbo_messagebox.hpp"
#include "d64_turbo_context_menu.hpp"
#include "d64_turbo_output.hpp"
#include <QApplication>
#include <QClipboard>
#include <QCloseEvent>
#include <QEvent>
#include <QFontMetrics>
#include <QHeaderView>
#include <QAbstractItemView>
#include <QTimer>
#include <QSizePolicy>
#include <QGridLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QMouseEvent>
#include <QPainter>
#include <QPlainTextEdit>
#include <QMenu>
#include <QAction>
#include <QKeySequence>
#include <QScrollBar>
#include <QPointer>
#include <QPushButton>
#include <QRandomGenerator>
#include <QTableWidget>
#include <QTableWidgetItem>
#include <QToolButton>
#include <QVBoxLayout>
#include <QWidget>
#include <functional>
#include <utility>
#include <algorithm>
#include <cmath>

class D64TurboToolWindow final : public QWidget {
public:
    enum Kind { Calculator, AsciiTable, Puzzle };
    explicit D64TurboToolWindow(QWidget *viewport, Kind kind)
        : QWidget(viewport), kind_(kind)
    {
        setAttribute(Qt::WA_StyledBackground, true);
        setAttribute(Qt::WA_DeleteOnClose, true);
        setObjectName(QStringLiteral("dbaseTurboToolWindow"));
        setFocusPolicy(Qt::StrongFocus);
        setMouseTracking(true);
        if (kind == Calculator) { preferredCols_ = 42; preferredRows_ = 19; }
        else if (kind == AsciiTable) { preferredCols_ = 62; preferredRows_ = 23; }
        else { preferredCols_ = 45; preferredRows_ = 22; }

        title_ = new QLabel(QStringLiteral(" %1 ").arg(windowName()), this);
        title_->setObjectName(QStringLiteral("dbaseTurboToolTitle"));
        title_->setAlignment(Qt::AlignCenter);
        title_->setCursor(Qt::SizeAllCursor);
        title_->setStyleSheet(QStringLiteral("background:#2457b9;color:#ffff55;font-weight:bold;"));
        title_->installEventFilter(this);
        close_ = new QToolButton(this);
        close_->setObjectName(QStringLiteral("dbaseTurboToolClose"));
        close_->setText(QStringLiteral("×"));
        close_->setToolTip(QStringLiteral("Fenster schließen"));
        maximize_ = new QToolButton(this);
        maximize_->setObjectName(QStringLiteral("dbaseTurboToolMaximize"));
        maximize_->setText(QStringLiteral("□"));
        maximize_->setToolTip(QStringLiteral("Maximieren"));
        for (QToolButton *button : {close_, maximize_}) {
            button->setFocusPolicy(Qt::NoFocus);
            button->setCursor(Qt::ArrowCursor);
            button->setStyleSheet(QStringLiteral(
                "QToolButton{color:#ffff55;background:#124299;border:1px solid #ffff55;"
                "font-weight:bold;padding:0;}"
                "QToolButton:hover{background:#397ad2;}"));
        }
        QObject::connect(close_, &QToolButton::clicked, this, [this]() { close(); });
        QObject::connect(maximize_, &QToolButton::clicked, this,
                         [this]() { toggleMaximized(); });
        content_ = new QWidget(this);
        content_->setObjectName(QStringLiteral("dbaseTurboToolContent"));
        content_->setStyleSheet(QStringLiteral(
            "QWidget#dbaseTurboToolContent{background:#0000aa;color:white;}"
            "QLabel{background:transparent;color:#ffff55;}"
            "QPushButton{background:#1640a9;color:#ffffff;border:1px solid #ffff55;"
            "padding:3px;font-weight:bold;}"
            "QPushButton:hover{background:#3664d0;}"
            "QPushButton:pressed{background:#454588;}"
            "QLineEdit{background:#000080;color:white;border:1px solid #ffff55;padding:5px;}"
            "QTableWidget{background:#000080;color:white;gridline-color:#7b85c0;"
            "border:1px solid #ffff55;selection-background-color:#a0a04c;selection-color:black;}"
            "QHeaderView::section{background:#2256af;color:#ffff55;"
            "border:1px solid #5555ac;}"
        ));
        buildContents();
        if (viewport) viewport->installEventFilter(this);
        hide();
    }
    QString windowName() const
    {
        switch (kind_) {
        case Calculator: return QStringLiteral("Taschenrechner");
        case AsciiTable: return QStringLiteral("ASCII-Zeichentabelle (CP437)");
        case Puzzle: return QStringLiteral("Puzzle (15)");
        }
        return QStringLiteral("Werkzeug");
    }
    void setActivationCallback(std::function<void(D64TurboToolWindow *)> callback)
    { onActivated_ = std::move(callback); }
    void setClosedCallback(std::function<void(D64TurboToolWindow *)> callback)
    { onClosed_ = std::move(callback); }
    void setGridFont(const QFont &font)
    {
        gridFont_ = font;
        const QFontMetrics fm(font);
        cellW_ = qMax(1, fm.horizontalAdvance(QLatin1Char('M')));
        cellH_ = qMax(1, fm.lineSpacing());
        title_->setFont(font);
        close_->setFont(font);
        maximize_->setFont(font);
        if (calculatorEdit_) calculatorEdit_->setFont(font);
        if (asciiTable_) asciiTable_->setFont(font);
        if (asciiStatus_) asciiStatus_->setFont(font);
        if (puzzleStatus_) puzzleStatus_->setFont(font);
        // Auch Tasten und Tabellenbeschriftungen folgen dem Zoomfaktor.
        for (QPushButton *button : content_->findChildren<QPushButton *>())
            if (button) button->setFont(font);
        applyGridGeometry();
    }
    void setInitialGridPosition(int column, int row)
    { column_ = column; row_ = row; applyGridGeometry(); }
    void setGridGeometry(int column, int row, int cols, int rows)
    {
        if (maximized_) toggleMaximized();
        column_ = column; row_ = row;
        preferredCols_ = qMax(24, cols);
        preferredRows_ = qMax(10, rows);
        applyGridGeometry();
    }
    void activate()
    {
        applyGridGeometry();
        show(); raise();
        if (onActivated_) onActivated_(this);
        if (calculatorEdit_) calculatorEdit_->setFocus(Qt::OtherFocusReason);
        else setFocus(Qt::OtherFocusReason);
    }
    bool isMaximizedInViewport() const { return maximized_; }
    void toggleMaximized()
    {
        if (!maximized_) {
            restoreCol_ = column_; restoreRow_ = row_;
            restoreCols_ = preferredCols_; restoreRows_ = preferredRows_;
            maximized_ = true;
            maximize_->setText(QStringLiteral("▣"));
            maximize_->setToolTip(QStringLiteral("Wiederherstellen"));
        } else {
            maximized_ = false;
            column_ = restoreCol_; row_ = restoreRow_;
            preferredCols_ = restoreCols_; preferredRows_ = restoreRows_;
            maximize_->setText(QStringLiteral("□"));
            maximize_->setToolTip(QStringLiteral("Maximieren"));
        }
        applyGridGeometry();
    }
protected:
    void paintEvent(QPaintEvent *) override
    {
        QPainter p(this);
        const int right = width() - shadow_ - 1;
        const int bottom = height() - shadow_ - 1;
        p.fillRect(QRect(shadow_, shadow_, width()-shadow_, height()-shadow_), QColor("#08082b"));
        p.fillRect(QRect(0,0,right+1,bottom+1), QColor("#0000aa"));
        p.setPen(QPen(QColor("#ffff55"),2));
        p.drawRect(1,1,right-2,bottom-2);
        p.setPen(QPen(QColor("#d8c840"),1));
        p.drawRect(4,4,right-8,bottom-8);
        p.fillRect(QRect(6,6,right-11,titleHeight()-7), QColor("#2457b9"));
    }
    void resizeEvent(QResizeEvent *event) override
    { QWidget::resizeEvent(event); layoutChildren(); }
    void closeEvent(QCloseEvent *event) override
    {
        if (onClosed_) onClosed_(this);
        QWidget::closeEvent(event);
    }
    void mousePressEvent(QMouseEvent *event) override
    {
        if (event->button() == Qt::LeftButton && titleHit(event->pos())) {
            activateOnClick();
            if (!maximized_) {
                dragging_ = true;
                dragStart_ = event->globalPos();
                startCol_ = column_; startRow_ = row_;
            }
            event->accept(); return;
        }
        QWidget::mousePressEvent(event);
    }
    void mouseMoveEvent(QMouseEvent *event) override
    {
        if (dragging_ && (event->buttons() & Qt::LeftButton)) {
            const QPoint delta = event->globalPos() - dragStart_;
            column_ = startCol_ + roundCell(delta.x(), cellW_);
            row_ = startRow_ + roundCell(delta.y(), cellH_);
            applyGridGeometry();
            event->accept(); return;
        }
        QWidget::mouseMoveEvent(event);
    }
    void mouseReleaseEvent(QMouseEvent *event) override
    {
        if (dragging_ && event->button() == Qt::LeftButton) {
            dragging_ = false; event->accept(); return;
        }
        QWidget::mouseReleaseEvent(event);
    }
    void mouseDoubleClickEvent(QMouseEvent *event) override
    {
        if (event->button() == Qt::LeftButton && titleHit(event->pos())) {
            toggleMaximized(); event->accept(); return;
        }
        QWidget::mouseDoubleClickEvent(event);
    }
    bool eventFilter(QObject *watched, QEvent *event) override
    {
        if (watched == parentWidget() && event->type() == QEvent::Resize) {
            QTimer::singleShot(0, this, [this]() { applyGridGeometry(); });
        }
        if (watched == title_) {
            if (event->type() == QEvent::MouseButtonDblClick) {
                toggleMaximized(); return true;
            }
            if (event->type() == QEvent::MouseButtonPress) {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (mouse->button() == Qt::LeftButton) {
                    activateOnClick();
                    if (!maximized_) {
                        dragging_ = true;
                        dragStart_ = mouse->globalPos();
                        startCol_ = column_; startRow_ = row_;
                    }
                    return true;
                }
            }
            if (event->type() == QEvent::MouseMove && dragging_) {
                auto *mouse = static_cast<QMouseEvent *>(event);
                if (mouse->buttons() & Qt::LeftButton) {
                    const QPoint delta = mouse->globalPos() - dragStart_;
                    column_ = startCol_ + roundCell(delta.x(), cellW_);
                    row_ = startRow_ + roundCell(delta.y(), cellH_);
                    applyGridGeometry(); return true;
                }
            }
            if (event->type() == QEvent::MouseButtonRelease && dragging_) {
                dragging_ = false; return true;
            }
        }
        return QWidget::eventFilter(watched,event);
    }
private:
    void activateOnClick() { raise(); if (onActivated_) onActivated_(this); }
    static int roundCell(int delta,int cell)
    {
        cell = qMax(1,cell);
        return delta >= 0 ? (delta + cell/2)/cell : -((-delta + cell/2)/cell);
    }
    bool titleHit(const QPoint &p) const
    { return p.x() >= 5 && p.y() >= 5 && p.x() < width()-shadow_-5 && p.y() < titleHeight(); }
    int titleHeight() const { return cellH_ + 14; }
    void applyGridGeometry()
    {
        if (!parentWidget()) return;
        if (maximized_) {
            setGeometry(QRect(QPoint(0,0), parentWidget()->size()));
            return;
        }
        const int viewCols = qMax(1,parentWidget()->width()/qMax(1,cellW_));
        const int viewRows = qMax(1,parentWidget()->height()/qMax(1,cellH_));
        column_ = qBound(0,column_,qMin(79,qMax(0,viewCols-qMin(10,viewCols))));
        row_ = qBound(0,row_,qMin(24,viewRows-1));
        setGeometry(column_*cellW_, row_*cellH_, preferredCols_*cellW_, preferredRows_*cellH_);
    }
    void layoutChildren()
    {
        const int right = qMax(20,width()-shadow_);
        const int bottom = qMax(20,height()-shadow_);
        const int tH = titleHeight();
        const int bh = qMax(15,cellH_);
        const int bw = qMax(22,cellW_*3);
        close_->setGeometry(8,qMax(5,(tH-bh)/2),bw,bh);
        maximize_->setGeometry(right-bw-8,qMax(5,(tH-bh)/2),bw,bh);
        title_->setGeometry(8+bw+3,6,qMax(1,right-2*bw-27),qMax(1,tH-10));
        content_->setGeometry(7,tH,qMax(1,right-14),qMax(1,bottom-tH-8));
        close_->raise(); maximize_->raise();
    }
    void buildContents()
    {
        if (kind_ == Calculator) buildCalculator();
        else if (kind_ == AsciiTable) buildAsciiTable();
        else buildPuzzle();
    }
    void buildCalculator()
    {
        auto *outer = new QVBoxLayout(content_);
        outer->setContentsMargins(7,7,7,7);
        outer->setSpacing(5);
        calculatorEdit_ = new QLineEdit(content_);
        calculatorEdit_->setObjectName(QStringLiteral("dbaseTurboCalculatorExpression"));
        calculatorEdit_->setAlignment(Qt::AlignRight);
        calculatorEdit_->setPlaceholderText(QStringLiteral("2 + 3 * 4"));
        calculatorEdit_->setContextMenuPolicy(Qt::CustomContextMenu);
        QObject::connect(calculatorEdit_, &QWidget::customContextMenuRequested, this,
                         [this](const QPoint &position) {
            showCalculatorContextMenu(calculatorEdit_->mapToGlobal(position));
        });
        // Auch ein Rechtsklick in die freie Rechnerflaeche soll das gleiche
        // deutschsprachige Kontextmenue anbieten.
        content_->setContextMenuPolicy(Qt::CustomContextMenu);
        QObject::connect(content_, &QWidget::customContextMenuRequested, this,
                         [this](const QPoint &position) {
            showCalculatorContextMenu(content_->mapToGlobal(position));
        });
        outer->addWidget(calculatorEdit_);
        QObject::connect(calculatorEdit_, &QLineEdit::returnPressed, this,
                         [this]() { evaluateCalculator(); });
        auto *keypad = new QGridLayout();
        keypad->setSpacing(5);
        const QStringList buttons = {
            QStringLiteral("C"), QStringLiteral("("), QStringLiteral(")"), QStringLiteral("/"),
            QStringLiteral("7"), QStringLiteral("8"), QStringLiteral("9"), QStringLiteral("*"),
            QStringLiteral("4"), QStringLiteral("5"), QStringLiteral("6"), QStringLiteral("-"),
            QStringLiteral("1"), QStringLiteral("2"), QStringLiteral("3"), QStringLiteral("+"),
            QStringLiteral("0"), QStringLiteral("."), QStringLiteral("←"), QStringLiteral("=")
        };
        for (int index = 0; index < buttons.size(); ++index) {
            const QString character = buttons.at(index);
            auto *button = new QPushButton(character, content_);
            button->setMinimumHeight(26);
            button->setObjectName(QStringLiteral("dbaseTurboCalculatorButton"));
            // Numerische Felder zeigen eine Hand an, andere Bedienelemente
            // behalten ihre bisherige Cursorform.
            if ((character.size() == 1 && character.at(0).isDigit())
                || character == QLatin1String("."))
                button->setCursor(Qt::PointingHandCursor);
            keypad->addWidget(button,index/4,index%4);
            QObject::connect(button, &QPushButton::clicked, this,[this,character]() {
                if (character == QLatin1String("=")) evaluateCalculator();
                else if (character == QLatin1String("C")) calculatorEdit_->clear();
                else if (character == QStringLiteral("←")) calculatorEdit_->backspace();
                else calculatorEdit_->insert(character);
                calculatorEdit_->setFocus(Qt::OtherFocusReason);
            });
        }
        outer->addLayout(keypad,1);
    }
    void showCalculatorContextMenu(const QPoint &globalPosition)
    {
        if (!calculatorEdit_) return;
        QMenu menu(calculatorEdit_);
        menu.setObjectName(QStringLiteral("dbaseTurboCalculatorContextMenu"));
        menu.setStyleSheet(d64TurboGreyContextMenuStyle());
        auto addEntry = [&menu](const QString &text, const QKeySequence &shortcut,
                                const std::function<void()> &callback) {
            QAction *action = menu.addAction(text);
            action->setShortcut(shortcut);
            action->setShortcutVisibleInContextMenu(true);
            QObject::connect(action, &QAction::triggered, &menu,
                             [callback](bool) { callback(); });
            return action;
        };
        addEntry(QStringLiteral("Rückgängig"), QKeySequence::Undo,
                 [this]() { calculatorEdit_->undo(); })
            ->setEnabled(calculatorEdit_->isUndoAvailable());
        addEntry(QStringLiteral("Wiederherstellen"),
                 QKeySequence(static_cast<int>(Qt::CTRL) | static_cast<int>(Qt::Key_Y)),
                 [this]() { calculatorEdit_->redo(); })
            ->setEnabled(calculatorEdit_->isRedoAvailable());
        menu.addSeparator();
        addEntry(QStringLiteral("Ausschneiden"), QKeySequence::Cut,
                 [this]() { calculatorEdit_->cut(); })
            ->setEnabled(calculatorEdit_->hasSelectedText());
        addEntry(QStringLiteral("Kopieren"), QKeySequence::Copy,
                 [this]() { calculatorEdit_->copy(); })
            ->setEnabled(calculatorEdit_->hasSelectedText());
        addEntry(QStringLiteral("Einfügen"), QKeySequence::Paste,
                 [this]() { calculatorEdit_->paste(); });
        addEntry(QStringLiteral("Löschen"), QKeySequence(Qt::Key_Delete),
                 [this]() { calculatorEdit_->del(); })
            ->setEnabled(calculatorEdit_->hasSelectedText());
        menu.addSeparator();
        addEntry(QStringLiteral("Alles auswählen"), QKeySequence::SelectAll,
                 [this]() { calculatorEdit_->selectAll(); });
        menu.exec(globalPosition);
    }
    void evaluateCalculator()
    {
        const auto result = D64CalculatorExpression::evaluate(calculatorEdit_->text().toStdString());
        if (!result.ok) {
            D64TurboMessageBox::information(this, QString::fromLatin1(result.error.c_str()),
                                            QStringLiteral("Rechenfehler"));
            return;
        }
        calculatorEdit_->setText(QString::number(result.value,'g',15));
        calculatorEdit_->selectAll();
    }
    void buildAsciiTable()
    {
        auto *outer = new QVBoxLayout(content_);
        outer->setContentsMargins(6,6,6,6);
        asciiStatus_ = new QLabel(QStringLiteral("CP437 · Zeichen auswählen · Doppelklick kopiert"),content_);
        asciiStatus_->setObjectName(QStringLiteral("dbaseTurboAsciiStatus"));
        outer->addWidget(asciiStatus_);
        asciiTable_ = new QTableWidget(16,16,content_);
        asciiTable_->setObjectName(QStringLiteral("dbaseTurboAsciiTable"));
        asciiTable_->setEditTriggers(QAbstractItemView::NoEditTriggers);
        asciiTable_->setSelectionMode(QAbstractItemView::SingleSelection);
        asciiTable_->setSelectionBehavior(QAbstractItemView::SelectItems);
        // Dieselben Turbo-Vision-Pfeilscrollbalken wie der Texteditor,
        // inklusive gemeinsamer Thumb-Begrenzung aus Stage 630.
        auto *asciiVertical = new D64TurboArrowScrollBar(Qt::Vertical, asciiTable_);
        asciiVertical->setObjectName(QStringLiteral("dbaseTurboAsciiVerticalScroll"));
        asciiVertical->setTurboEditorTheme();
        asciiVertical->setCursor(Qt::ArrowCursor);
        asciiTable_->setVerticalScrollBar(asciiVertical);
        auto *asciiHorizontal = new D64TurboArrowScrollBar(Qt::Horizontal, asciiTable_);
        asciiHorizontal->setObjectName(QStringLiteral("dbaseTurboAsciiHorizontalScroll"));
        asciiHorizontal->setTurboEditorTheme();
        asciiHorizontal->setCursor(Qt::ArrowCursor);
        asciiTable_->setHorizontalScrollBar(asciiHorizontal);
        asciiTable_->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOn);
        asciiTable_->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOn);
        asciiTable_->verticalHeader()->setDefaultSectionSize(28);
        asciiTable_->horizontalHeader()->setDefaultSectionSize(32);
        QStringList headings;
        for (int n = 0; n < 16; ++n) headings << QString::number(n,16).toUpper();
        asciiTable_->setHorizontalHeaderLabels(headings);
        asciiTable_->setVerticalHeaderLabels(headings);
        for (int code = 0; code < 256; ++code) {
            QChar glyph = D64TurboOutputWidget::dosCharacter(code);
            // Steuerzeichen bleiben als grafische DOS-Zeichen dargestellt;
            // Code 00 zeigt ein sichtbares Leerzeichen.
            auto *item = new QTableWidgetItem(QString(glyph));
            item->setTextAlignment(Qt::AlignCenter);
            item->setData(Qt::UserRole,code);
            item->setToolTip(QStringLiteral("Dez: %1 · Hex: %2")
                .arg(code).arg(code,2,16,QLatin1Char('0')).toUpper());
            asciiTable_->setItem(code/16,code%16,item);
        }
        QObject::connect(asciiTable_, &QTableWidget::cellClicked, this,
                         [this](int row,int col) {
            const int code = row*16+col;
            asciiStatus_->setText(QStringLiteral("Dezimal: %1    Hex: %2    Zeichen: %3")
                        .arg(code).arg(code,2,16,QLatin1Char('0')).toUpper()
                        .arg(D64TurboOutputWidget::dosCharacter(code)));
        });
        QObject::connect(asciiTable_, &QTableWidget::cellDoubleClicked, this,
                         [this](int row,int col) {
            QApplication::clipboard()->setText(QString(D64TurboOutputWidget::dosCharacter(row*16+col)));
        });
        outer->addWidget(asciiTable_,1);
    }
    void buildPuzzle()
    {
        auto *outer = new QVBoxLayout(content_);
        outer->setContentsMargins(7,7,7,7);
        puzzleStatus_ = new QLabel(QStringLiteral("15-Puzzle · Steine in Reihenfolge bringen"),content_);
        puzzleStatus_->setObjectName(QStringLiteral("dbaseTurboPuzzleStatus"));
        puzzleStatus_->setAlignment(Qt::AlignCenter);
        outer->addWidget(puzzleStatus_);
        auto *board = new QGridLayout();
        board->setSpacing(5);
        for (int tile = 0; tile < 16; ++tile) {
            puzzle_[tile] = (tile==15 ? 0 : tile+1);
            auto *button = new QPushButton(content_);
            button->setObjectName(QStringLiteral("dbaseTurboPuzzleTile"));
            button->setMinimumSize(30,30);
            button->setSizePolicy(QSizePolicy::Expanding,QSizePolicy::Expanding);
            puzzleButtons_.append(button);
            board->addWidget(button,tile/4,tile%4);
            QObject::connect(button, &QPushButton::clicked, this,
                             [this,tile]() { movePuzzleTile(tile); });
        }
        outer->addLayout(board,1);
        auto *shuffle = new QPushButton(QStringLiteral("Neu mischen"), content_);
        shuffle->setObjectName(QStringLiteral("dbaseTurboPuzzleShuffle"));
        QObject::connect(shuffle, &QPushButton::clicked, this,
                         [this]() { shufflePuzzle(); });
        outer->addWidget(shuffle);
        shufflePuzzle();
    }
    void shufflePuzzle()
    {
        for (int i = 0; i < 16; ++i) puzzle_[i] = i==15 ? 0 : i+1;
        int blank = 15;
        int prior = -1;
        for (int step = 0; step < 180; ++step) {
            QList<int> choices;
            const int r=blank/4,c=blank%4;
            if (r>0 && blank-4!=prior) choices << blank-4;
            if (r<3 && blank+4!=prior) choices << blank+4;
            if (c>0 && blank-1!=prior) choices << blank-1;
            if (c<3 && blank+1!=prior) choices << blank+1;
            if (choices.isEmpty()) { prior=-1; --step; continue; }
            const int chosen=choices.at(QRandomGenerator::global()->bounded(choices.size()));
            std::swap(puzzle_[blank],puzzle_[chosen]);
            prior=blank;blank=chosen;
        }
        // Gelegentlich entsteht die geordnete Position. In diesem Fall einen
        // zulaessigen Schritt ausfuehren, damit ein Spiel beginnt.
        if (puzzleSolved()) std::swap(puzzle_[15],puzzle_[14]);
        moves_=0;renderPuzzle();
    }
    void movePuzzleTile(int index)
    {
        int blank=0;
        for (;blank<16 && puzzle_[blank]!=0;++blank) {}
        if (index < 0 || index>=16 || blank>=16) return;
        if (std::abs(index/4-blank/4)+std::abs(index%4-blank%4)!=1) return;
        std::swap(puzzle_[blank],puzzle_[index]);
        ++moves_;renderPuzzle();
        if (puzzleSolved()) D64TurboMessageBox::information(
            this, QStringLiteral("Geschafft! Das Puzzle ist nach %1 Zügen gelöst.").arg(moves_));
    }
    bool puzzleSolved() const
    {
        for (int i=0;i<15;++i) if (puzzle_[i]!=i+1) return false;
        return puzzle_[15]==0;
    }
    void renderPuzzle()
    {
        for (int i=0;i<16;++i) {
            QPushButton *button=puzzleButtons_.at(i);
            button->setText(puzzle_[i]==0 ? QString() : QString::number(puzzle_[i]));
            button->setEnabled(puzzle_[i]!=0);
            button->setVisible(true);
        }
        puzzleStatus_->setText(QStringLiteral("15-Puzzle  ·  Züge: %1").arg(moves_));
    }
    Kind kind_;
    QWidget *content_ = nullptr;
    QLabel *title_ = nullptr;
    QToolButton *close_ = nullptr;
    QToolButton *maximize_ = nullptr;
    QLineEdit *calculatorEdit_ = nullptr;
    QTableWidget *asciiTable_ = nullptr;
    QLabel *asciiStatus_ = nullptr;
    QLabel *puzzleStatus_ = nullptr;
    QList<QPushButton *> puzzleButtons_;
    int puzzle_[16] = {};
    int moves_ = 0;
    QFont gridFont_;
    std::function<void(D64TurboToolWindow *)> onActivated_;
    std::function<void(D64TurboToolWindow *)> onClosed_;
    int cellW_ = 9,cellH_ = 16;
    int preferredCols_ = 42,preferredRows_ = 19;
    int column_ = 5,row_ = 3;
    int restoreCol_ = 5, restoreRow_ = 3,restoreCols_ = 42,restoreRows_ = 19;
    static constexpr int shadow_ = 7;
    bool maximized_ = false,dragging_ = false;
    QPoint dragStart_;
    int startCol_ = 0,startRow_ = 0;
};
